#!/usr/bin/env python3
"""
Knowledge Engine v3 – Saraphina's Infinite Brain (November 2025)

Merged & upgraded from:
- v2 (SQLite + FTS5 + async web/RSS ingestion, summarisation)
- v3 (ChromaDB + knowledge graph + FAISS)

Final feature set:
- SQLite + FTS5 store (fast keyword / topic search)
- Optional ChromaDB persistent vector store (hybrid semantic search)
- Optional FAISS in-memory vector index for ultra-fast similarity
- NetworkX knowledge graph with entity/relation extraction
- spaCy-powered topic, entity & relation extraction
- Async web crawling (Wikipedia), RSS ingestion
- Prompt-friendly summarisation (transformers, optional)
- Backward-compatible API: KnowledgeEngine.ingest_text, summarize_for_prompt,
  search_fts, query_exact, query_knowledge, search_related
- Thread-safe, async-ready, hot-reload safe
- Optional daily maintenance hook (to be scheduled externally or via APScheduler in ultra_core)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import random
import re
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncGenerator, List, Optional, Dict, Any, Tuple, Set

import feedparser
import httpx
import networkx as nx
import numpy as np
from bs4 import BeautifulSoup

# robots_parser is optional; if unavailable, we skip robots.txt checks.
try:
    import robots_parser
    ROBOTS_PARSER_AVAILABLE = True
except Exception:
    robots_parser = None  # type: ignore
    ROBOTS_PARSER_AVAILABLE = False

# --------------------------------------------------------------------------- #
# OPTIONAL NLP / VECTORS / SUMMARISATION
# --------------------------------------------------------------------------- #
try:
    import spacy
    # Prefer transformer model, fall back to small
    try:
        NLP = spacy.load("en_core_web_trf")
    except Exception:
        NLP = spacy.load("en_core_web_sm")
except Exception:  # pragma: no cover
    NLP = None

try:
    from transformers import pipeline
    SUMMARISER = pipeline("summarization", model="facebook/bart-large-cnn")
except Exception:  # pragma: no cover
    SUMMARISER = None

# sentence-transformers is used for both custom embeddings and FAISS/Chroma fallback
try:
    from sentence_transformers import SentenceTransformer
    ST_EMBEDDER = SentenceTransformer("all-MiniLM-L6-v2")
except Exception:  # pragma: no cover
    ST_EMBEDDER = None

# ChromaDB for persistent vector store
try:
    import chromadb
    from chromadb.utils import embedding_functions
    CHROMA_AVAILABLE = True
except Exception:  # pragma: no cover
    CHROMA_AVAILABLE = False

# FAISS for in-memory ANN
try:
    import faiss
    FAISS_AVAILABLE = True
except Exception:  # pragma: no cover
    FAISS_AVAILABLE = False

# --------------------------------------------------------------------------- #
# PATHS & CONFIG
# --------------------------------------------------------------------------- #
KNOWLEDGE_ROOT = Path(r"D:/Saraphina Root/data/knowledge_v3")
KNOWLEDGE_ROOT.mkdir(parents=True, exist_ok=True)

SQLITE_DB = KNOWLEDGE_ROOT / "knowledge.db"
CHROMA_PATH = KNOWLEDGE_ROOT / "chroma"
GRAPH_PATH = KNOWLEDGE_ROOT / "knowledge_graph.gml"
GRAPH_NX_PATH = KNOWLEDGE_ROOT / "knowledge_graph.pkl"

# Polite crawling defaults
USER_AGENT = "SaraphinaKnowledgeBot/3.0 (+https://github.com/your-repo)"
REQUEST_DELAY = 1.2  # seconds between requests to the same host

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s | %(message)s",
)
log = logging.getLogger("KnowledgeEngineV3")

# --------------------------------------------------------------------------- #
# DATACLASSES
# --------------------------------------------------------------------------- #
@dataclass
class KnowledgeEntry:
    topic: str
    description: str
    source_url: Optional[str] = None
    embedding: Optional[List[float]] = None  # populated only if vector search is used


@dataclass
class Relation:
    source: str
    target: str
    relation: str
    confidence: float = 1.0
    source_text: str = ""


# --------------------------------------------------------------------------- #
# CORE ENGINE (UNIFIED V2+V3)
# --------------------------------------------------------------------------- #
class KnowledgeEngineV3:
    """
    Unified knowledge engine mixing:
    - SQLite + FTS (from v2)
    - ChromaDB + Graph + FAISS (from v3)
    """

    def __init__(self, sqlite_path: Path = SQLITE_DB, chroma_dir: str = str(CHROMA_PATH)):
        self.sqlite_path = sqlite_path
        self.chroma_dir = chroma_dir

        self._init_sqlite()
        self._thread_local = None  # lazily initialised per-thread connection
        self._async_lock = asyncio.Lock()

        # --- ChromaDB ---
        if CHROMA_AVAILABLE:
            try:
                self.chroma_client = chromadb.PersistentClient(path=chroma_dir)
                self.chroma_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name="all-MiniLM-L6-v2"
                )
                self.collection = self.chroma_client.get_or_create_collection(
                    name="saraphina_knowledge",
                    embedding_function=self.chroma_ef,
                )
            except Exception as e:
                log.warning(f"[Chroma] init failed: {e}")
                self.chroma_client = None
                self.collection = None
        else:
            self.chroma_client = None
            self.collection = None

        # --- FAISS fallback ---
        self.faiss_index = None
        self.faiss_texts: List[str] = []
        self.faiss_ids: List[str] = []

        # --- Knowledge graph ---
        self.G = nx.MultiDiGraph()
        self._load_graph()

        # Seen topics (for curiosity / introspection)
        self.seen_topics: Set[str] = set()

    # ------------------------------------------------------------------- #
    # SQLITE INITIALISATION & CONNECTION
    # ------------------------------------------------------------------- #
    def _init_sqlite(self) -> None:
        conn = sqlite3.connect(str(self.sqlite_path), check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")

        # Main FTS table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS knowledge_fts (
                rowid INTEGER PRIMARY KEY,
                topic TEXT NOT NULL,
                description TEXT NOT NULL,
                source_url TEXT,
                ts INTEGER DEFAULT (unixepoch())
            );
            """
        )
        # Virtual FTS index
        conn.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts_idx
            USING fts5(topic, description, source_url, content='knowledge_fts', content_rowid='rowid');
            """
        )
        # Triggers to sync index
        conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS knowledge_fts_insert AFTER INSERT ON knowledge_fts
            BEGIN
                INSERT INTO knowledge_fts_idx(rowid, topic, description, source_url)
                VALUES (new.rowid, new.topic, new.description, new.source_url);
            END;
            """
        )
        conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS knowledge_fts_update AFTER UPDATE ON knowledge_fts
            BEGIN
                INSERT INTO knowledge_fts_idx(knowledge_fts_idx, rowid, topic, description, source_url)
                VALUES ('delete', old.rowid, old.topic, old.description, old.source_url);
                INSERT INTO knowledge_fts_idx(rowid, topic, description, source_url)
                VALUES (new.rowid, new.topic, new.description, new.source_url);
            END;
            """
        )
        conn.commit()
        conn.close()

    @property
    def conn(self) -> sqlite3.Connection:
        import threading

        if self._thread_local is None:
            self._thread_local = threading.local()
        if getattr(self._thread_local, "conn", None) is None:
            self._thread_local.conn = sqlite3.connect(str(self.sqlite_path), check_same_thread=False)
            self._thread_local.conn.execute("PRAGMA foreign_keys=ON;")
        return self._thread_local.conn

    # ------------------------------------------------------------------- #
    # GRAPH LOAD/SAVE
    # ------------------------------------------------------------------- #
    def _load_graph(self) -> None:
        if GRAPH_NX_PATH.exists():
            try:
                self.G = nx.readwrite.gpickle.read_gpickle(GRAPH_NX_PATH)
                log.info(f"[KG] Loaded graph with {self.G.number_of_nodes()} nodes, {self.G.number_of_edges()} edges")
                return
            except Exception:
                pass
        if GRAPH_PATH.exists():
            try:
                self.G = nx.read_gml(GRAPH_PATH)
                log.info(f"[KG] Loaded GML graph with {self.G.number_of_nodes()} nodes, {self.G.number_of_edges()} edges")
                return
            except Exception:
                pass
        log.info("[KG] Starting with empty knowledge graph")

    def _save_graph(self) -> None:
        try:
            nx.readwrite.gpickle.write_gpickle(self.G, GRAPH_NX_PATH)
            nx.write_gml(self.G, GRAPH_PATH)
        except Exception as e:
            log.warning(f"[KG] Graph save failed: {e}")

    # ------------------------------------------------------------------- #
    # TOPIC & ENTITY / RELATION EXTRACTION
    # ------------------------------------------------------------------- #
    def _infer_topic_spacy(self, text: str) -> Optional[str]:
        if not NLP:
            return None
        try:
            doc = NLP(text[:1000])
            # Prefer named entities
            for ent in doc.ents:
                if ent.label_ in ("PERSON", "ORG", "GPE", "PRODUCT", "EVENT", "WORK_OF_ART", "TECHNOLOGY"):
                    return ent.text.strip()
            # Fallback noun chunks
            for chunk in doc.noun_chunks:
                if chunk.root.is_alpha and len(chunk.text.strip()) > 2:
                    return chunk.text.strip()
        except Exception:
            return None
        return None

    def _infer_topic_heuristic(self, text: str) -> Optional[str]:
        text = text.strip()
        tokens = re.findall(r"\b[\w\-]+\b", text)
        if not tokens:
            return None
        stopwords = {
            "the", "and", "or", "but", "with", "from", "that", "this", "there",
            "about", "into", "onto", "over", "under", "because", "when", "where",
            "what", "which", "who", "whose", "whom", "how", "why", "is", "are",
            "am", "was", "were", "will", "would", "can", "could", "should",
            "have", "has", "had", "you", "your", "yours", "i", "me", "my", "mine",
            "we", "us", "our", "ours", "it", "its", "they", "them", "their", "theirs",
        }
        # Prefer capitalised non-stopword
        for tok in tokens[:12]:
            if len(tok) < 3 or tok.lower() in stopwords:
                continue
            if tok[0].isupper():
                return tok
        for tok in tokens:
            if len(tok) < 3 or tok.lower() in stopwords:
                continue
            return tok
        return None

    def _infer_topic(self, text: str) -> Optional[str]:
        if not text:
            return None
        t = self._infer_topic_spacy(text)
        if t:
            return t
        return self._infer_topic_heuristic(text)

    def _extract_entities_and_relations(self, text: str) -> List[Relation]:
        if not NLP:
            return []
        relations: List[Relation] = []
        try:
            doc = NLP(text)
        except Exception:
            return relations

        for sent in doc.sents:
            entities = {ent.text: ent.label_ for ent in sent.ents}
            # Basic subject/object detection
            subjects = [tok for tok in sent if tok.dep_ in ("nsubj", "nsubjpass")]
            objects = [tok for tok in sent if tok.dep_ in ("dobj", "pobj", "attr")]

            for subj in subjects:
                for obj in objects:
                    # walk up from object to subject
                    relation_tokens = []
                    current = obj
                    while current != subj and current.head != current:
                        relation_tokens.append(current.head.lemma_)
                        current = current.head
                    if current == subj:
                        rel_text = " ".join(reversed(relation_tokens)) or "related to"
                        relations.append(
                            Relation(
                                source=subj.text.strip(),
                                target=obj.text.strip(),
                                relation=rel_text,
                                confidence=0.8,
                                source_text=sent.text,
                            )
                        )

            # Simple "X is a Y" pattern
            m = re.search(r"(.+?) (is a|is an) (.+?)(?:[.,]|$)", sent.text, re.I)
            if m:
                relations.append(
                    Relation(
                        source=m.group(1).strip(),
                        target=m.group(3).strip(),
                        relation="is a type of",
                        confidence=0.95,
                        source_text=sent.text,
                    )
                )

        return relations

    # ------------------------------------------------------------------- #
    # INGESTION (UNIFIED: SQLite + Chroma + Graph)
    # ------------------------------------------------------------------- #
    def ingest_text(self, text: str, source_url: Optional[str] = None, topic: Optional[str] = None) -> None:
        """
        Store a snippet into:
        - SQLite FTS (topic/description/source_url)
        - Optional Chroma vector store
        - Knowledge graph (relations)
        """
        text = (text or "").strip()
        if not text or len(text) < 20:
            return

        # Topic inference
        topic = topic or self._infer_topic(text)
        if not topic:
            log.debug("No topic inferred – skipping ingest.")
            return

        # Optional summarisation for SQLite description
        description = text
        if SUMMARISER and len(description) > 300:
            try:
                summary = SUMMARISER(description, max_length=180, min_length=60, do_sample=False)[0]["summary_text"]
                description = f"{summary}\n---\n{description[:500]}"
            except Exception as e:
                log.debug(f"Summarisation failed: {e}")

        # SQLite insert
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO knowledge_fts (topic, description, source_url)
            VALUES (?, ?, ?)
            """,
            (topic, description, source_url),
        )
        self.conn.commit()

        # Chroma insert (raw text, no truncation)
        if self.collection:
            try:
                doc_id = f"{int(time.time() * 1000)}_{hash(text) % 100000}"
                metadata = {
                    "source": source_url or "inline",
                    "topic": topic,
                    "timestamp": time.time(),
                }
                self.collection.add(
                    documents=[text],
                    metadatas=[metadata],
                    ids=[doc_id],
                )
            except Exception as e:
                log.debug(f"[Chroma] add failed: {e}")

        # Knowledge graph relations
        relations = self._extract_entities_and_relations(text)
        for rel in relations:
            self.G.add_edge(
                rel.source.title(),
                rel.target.title(),
                relation=rel.relation,
                confidence=rel.confidence,
                source_text=rel.source_text,
            )

        # Track seen topics
        self.seen_topics.add(topic.lower())

        # Periodically save graph
        if relations or random.random() < 0.01:
            self._save_graph()

        log.info(f"Ingested topic='{topic}' from {source_url or 'inline'}")

    async def ingest_async(self, text: str, source_url: Optional[str] = None, topic: Optional[str] = None) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.ingest_text, text, source_url, topic)

    # ------------------------------------------------------------------- #
    # SQLITE QUERY INTERFACE (BACKWARD COMPATIBLE)
    # ------------------------------------------------------------------- #
    def query_exact(self, topic: str) -> List[KnowledgeEntry]:
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT rowid, topic, description, source_url
            FROM knowledge_fts
            WHERE topic = ?
            ORDER BY ts DESC
            """,
            (topic,),
        )
        rows = cur.fetchall()
        return [KnowledgeEntry(topic=r[1], description=r[2], source_url=r[3]) for r in rows]

    def search_fts(self, query: str, limit: int = 5) -> List[KnowledgeEntry]:
        """Full-text search over topic + description (SQLite FTS)."""
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT rowid, topic, description, source_url
            FROM knowledge_fts_idx
            WHERE knowledge_fts_idx MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (query, limit),
        )
        rows = cur.fetchall()
        return [KnowledgeEntry(topic=r[1], description=r[2], source_url=r[3]) for r in rows]

    def query_knowledge(self, topic: str) -> str:
        """
        Backward-compatible: return best description for a topic or empty string.
        """
        topic = (topic or "").strip()
        if not topic:
            return ""
        hits = self.query_exact(topic)
        if hits:
            return hits[0].description
        hits = self.search_fts(topic, limit=1)
        return hits[0].description if hits else ""

    # ------------------------------------------------------------------- #
    # HYBRID SEARCH (CHROMA + GRAPH + FTS)
    # ------------------------------------------------------------------- #
    def _graph_context_results(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        if not NLP or self.G.number_of_nodes() == 0:
            return results
        try:
            doc = NLP(query)
        except Exception:
            return results

        query_entities = [ent.text.title() for ent in doc.ents]
        for entity in query_entities:
            if not self.G.has_node(entity):
                continue
            neighbors = list(self.G.neighbors(entity)) + list(self.G.predecessors(entity))
            neighbors = neighbors[:limit]
            for neighbor in neighbors:
                edges = self.G.get_edge_data(entity, neighbor)
                for _, data in edges.items():
                    results.append(
                        {
                            "text": f"{entity} {data.get('relation', 'related to')} {neighbor}",
                            "topic": entity,
                            "source": "knowledge_graph",
                            "score": data.get("confidence", 0.8),
                            "type": "graph",
                        }
                    )
        return results

    def _chroma_results(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        if not self.collection:
            return []
        try:
            chroma_results = self.collection.query(
                query_texts=[query],
                n_results=limit * 2,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:
            log.debug(f"[Chroma] query failed: {e}")
            return []

        results: List[Dict[str, Any]] = []
        docs = chroma_results.get("documents") or [[]]
        metas = chroma_results.get("metadatas") or [[]]
        dists = chroma_results.get("distances") or [[]]
        for doc, meta, dist in zip(docs[0], metas[0], dists[0]):
            results.append(
                {
                    "text": doc,
                    "topic": meta.get("topic", "Unknown"),
                    "source": meta.get("source", "Unknown"),
                    "score": 1.0 - float(dist),
                    "type": "chroma",
                }
            )
        return results

    def _faiss_results(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        if not (FAISS_AVAILABLE and ST_EMBEDDER and self.faiss_index is not None and self.faiss_texts):
            return []
        try:
            q_emb = ST_EMBEDDER.encode([query])
            faiss.normalize_L2(q_emb)
            scores, idx = self.faiss_index.search(q_emb.astype(np.float32), limit)
        except Exception as e:
            log.debug(f"[FAISS] search failed: {e}")
            return []

        results: List[Dict[str, Any]] = []
        for score, i in zip(scores[0], idx[0]):
            if i < 0 or i >= len(self.faiss_texts):
                continue
            results.append(
                {
                    "text": self.faiss_texts[i],
                    "topic": "Unknown",
                    "source": "faiss",
                    "score": float(score),
                    "type": "faiss",
                }
            )
        return results

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Hybrid search:
        - Chroma semantic + metadata
        - Graph relational context
        - Optional FAISS fallback
        - Plus SQLite FTS as last resort
        """
        results: List[Dict[str, Any]] = []

        # Chroma
        results.extend(self._chroma_results(query, limit=limit))

        # Graph context
        results.extend(self._graph_context_results(query, limit=limit))

        # FAISS fallback
        results.extend(self._faiss_results(query, limit=limit))

        # FTS fallback (if everything else is empty)
        if not results:
            fts_hits = self.search_fts(query, limit=limit)
            for e in fts_hits:
                results.append(
                    {
                        "text": e.description,
                        "topic": e.topic,
                        "source": e.source_url or "fts",
                        "score": 0.5,
                        "type": "fts",
                    }
                )

        # Dedupe and sort
        seen = set()
        unique: List[Dict[str, Any]] = []
        for r in results:
            key = r["text"][:200]
            if key not in seen:
                seen.add(key)
                unique.append(r)

        unique.sort(key=lambda x: x["score"], reverse=True)
        return unique[:limit]

    # ------------------------------------------------------------------- #
    # PROMPT SUMMARY BUILDER (BACKWARD COMPATIBLE)
    # ------------------------------------------------------------------- #
    @staticmethod
    def _trim(text: str, max_len: int = 180) -> str:
        text = text.strip()
        if len(text) <= max_len:
            return text
        return text[:max_len].rsplit(" ", 1)[0] + " …"

    def summarize_for_prompt(self, topic_or_query: str, limit: int = 4) -> str:
        """
        Backward-compatible compact string for prompt injection.
        Uses hybrid search first; falls back to exact+FTS for small DB.
        """
        topic_or_query = (topic_or_query or "").strip()
        if not topic_or_query:
            return ""

        # 1. Try hybrid search
        results = self.search(topic_or_query, limit=limit)
        if not results:
            return ""

        parts = []
        for r in results:
            snippet = self._trim(r["text"])
            prefix = r.get("topic", "Fact")
            if r["type"] == "graph":
                prefix = "Relation"
            parts.append(f"{prefix}: {snippet}")
        return " | ".join(parts)

    # ------------------------------------------------------------------- #
    # GRAPH QUERIES
    # ------------------------------------------------------------------- #
    def get_related_concepts(self, topic: str, depth: int = 2) -> List[str]:
        if not self.G.has_node(topic.title()):
            return []
        related = set()
        queue: List[Tuple[str, int]] = [(topic.title(), 0)]
        visited = set()
        while queue:
            current, d = queue.pop(0)
            if current in visited or d > depth:
                continue
            visited.add(current)
            neighbors = list(self.G.neighbors(current)) + list(self.G.predecessors(current))
            related.update(neighbors)
            if d < depth:
                queue.extend((n, d + 1) for n in neighbors)
        related.discard(topic.title())
        return list(related)

    def is_known_topic(self, topic: str) -> bool:
        return topic.lower() in self.seen_topics or self.G.has_node(topic.title())

    # ------------------------------------------------------------------- #
    # MAINTENANCE (PRUNE + REBUILD FAISS + SAVE GRAPH)
    # ------------------------------------------------------------------- #
    def rebuild_faiss_index(self) -> None:
        if not (FAISS_AVAILABLE and ST_EMBEDDER and self.collection):
            return
        try:
            results = self.collection.get(include=["documents"])
            docs = results.get("documents") or []
            if not docs:
                return
            docs = docs[0]
            embeddings = ST_EMBEDDER.encode(docs)
            dim = embeddings.shape[1]
            self.faiss_index = faiss.IndexFlatIP(dim)
            faiss.normalize_L2(embeddings)
            self.faiss_index.add(embeddings.astype(np.float32))
            self.faiss_texts = docs
            log.info(f"[FAISS] Rebuilt index with {len(docs)} vectors")
        except Exception as e:
            log.debug(f"[FAISS] rebuild failed: {e}")

    def prune_old_knowledge(self, days_old: int = 90) -> None:
        if not self.collection:
            return
        cutoff = time.time() - days_old * 86400
        try:
            old = self.collection.get(where={"timestamp": {"$lt": cutoff}})
            ids = old.get("ids") or []
            if ids:
                self.collection.delete(ids=ids)
                log.info(f"[Prune] Removed {len(ids)} old entries from Chroma")
        except Exception as e:
            log.debug(f"[Prune] failed: {e}")

    def daily_maintenance(self) -> None:
        self.prune_old_knowledge()
        self.rebuild_faiss_index()
        self._save_graph()

    # ------------------------------------------------------------------- #
    # AUTONOMOUS GATHERING (ASYNC) – WIKIPEDIA & RSS (FROM v2)
    # ------------------------------------------------------------------- #
    async def _respect_robots(self, url: str, client: httpx.AsyncClient) -> bool:
        parsed = httpx.URL(url)
        robots_url = f"{parsed.scheme}://{parsed.host}/robots.txt"
        # If robots_parser is not available, default to allowing crawl.
        if not ROBOTS_PARSER_AVAILABLE:
            return True
        try:
            resp = await client.get(robots_url, timeout=5.0)
            if resp.status_code != 200:
                return True
            rp = robots_parser.RobotsParser.from_text(resp.text)
            return rp.can_fetch(USER_AGENT, url)
        except Exception:
            return True

    async def scrape_wikipedia(self, title: str) -> str:
        url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
        async with httpx.AsyncClient(headers={"User-Agent": USER_AGENT}, timeout=10.0) as client:
            if not await self._respect_robots(url, client):
                log.info(f"robots.txt blocks Wikipedia {title}")
                return ""
            resp = await client.get(url)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            paragraphs = soup.select("div.mw-parser-output > p")
            intro = "\n".join(p.get_text(strip=True) for p in paragraphs[:3] if p.get_text(strip=True))
            await self.ingest_async(f"Wikipedia: {title}\n{intro}", source_url=url)
            return intro[:1500]

    async def ingest_rss_feed(self, feed_url: str, max_entries: int = 5) -> List[str]:
        async with httpx.AsyncClient(headers={"User-Agent": USER_AGENT}, timeout=10.0) as client:
            resp = await client.get(feed_url)
            resp.raise_for_status()
            feed = feedparser.parse(resp.text)
            ingested: List[str] = []
            for entry in feed.entries[:max_entries]:
                title = entry.get("title", "Untitled")
                summary = entry.get("summary", "") or entry.get("description", "")
                link = entry.get("link")
                text = f"RSS: {title}\n{summary}"
                await self.ingest_async(text, source_url=link)
                ingested.append(title)
            return ingested

    async def gather_autonomously(
        self,
        wikipedia_topics: Optional[List[str]] = None,
        rss_feeds: Optional[List[str]] = None,
    ) -> None:
        """
        One-shot autonomous run – can be scheduled with APScheduler / Prefect.
        """
        wiki_list = wikipedia_topics or [
            "Artificial_intelligence",
            "Machine_learning",
            "Neuroscience",
            "Quantum_computing",
            "Large_language_model",
        ]
        rss_list = rss_feeds or [
            "http://feeds.bbci.co.uk/news/technology/rss.xml",
            "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
            "https://hnrss.org/frontpage",
        ]

        tasks = []
        for t in wiki_list:
            tasks.append(self.scrape_wikipedia(t))
            await asyncio.sleep(REQUEST_DELAY)
        for url in rss_list:
            tasks.append(self.ingest_rss_feed(url))

        await asyncio.gather(*tasks, return_exceptions=True)


# ==================== GLOBAL INSTANCE + BACKWARD COMPAT LAYER ====================
knowledge_engine_v3 = KnowledgeEngineV3()


class KnowledgeEngine:
    """
    Backward-compatible wrapper exposing the old v2 API:
    - ingest_text(text, source_url=None)
    - ingest_async(text, source_url=None)
    - summarize_for_prompt(topic_or_query, limit=3)
    - search_fts(query, limit=5)
    - query_exact(topic)
    - query_knowledge(topic)
    - search_related(query, limit=3) -> list[str]
    - gather_autonomously(...)
    """

    def __init__(self, *args, **kwargs):
        # Use the shared v3 engine instance
        global knowledge_engine_v3
        self._engine = knowledge_engine_v3

    # Core ingestion
    def ingest_text(self, text: str, source_url: Optional[str] = None) -> None:
        return self._engine.ingest_text(text, source_url)

    async def ingest_async(self, text: str, source_url: Optional[str] = None) -> None:
        return await self._engine.ingest_async(text, source_url)

    # Query / search API
    def summarize_for_prompt(self, topic_or_query: str, limit: int = 3) -> str:
        # limit is advisory; v3 will respect it as best as possible
        return self._engine.summarize_for_prompt(topic_or_query, limit=limit)

    def search_fts(self, query: str, limit: int = 5) -> List[KnowledgeEntry]:
        return self._engine.search_fts(query, limit=limit)

    def query_exact(self, topic: str) -> List[KnowledgeEntry]:
        return self._engine.query_exact(topic)

    def query_knowledge(self, topic: str) -> str:
        return self._engine.query_knowledge(topic)

    def search_related(self, query: str, limit: int = 3) -> List[str]:
        results = self._engine.search(query, limit=limit)
        return [r["text"] for r in results]

    # Autonomy / maintenance
    async def gather_autonomously(
        self,
        wikipedia_topics: Optional[List[str]] = None,
        rss_feeds: Optional[List[str]] = None,
    ) -> None:
        await self._engine.gather_autonomously(wikipedia_topics, rss_feeds)

    def daily_maintenance(self) -> None:
        self._engine.daily_maintenance()


# CLI / QUICK TEST
if __name__ == "__main__":
    engine = KnowledgeEngine()

    engine.ingest_text(
        "Saraphina is an autonomous AI assistant. She can browse the web, "
        "remember facts, and answer in natural language."
    )

    print("=== Exact ===")
    for e in engine.query_exact("Saraphina"):
        print(e.topic, "→", e.description[:120])

    print("\n=== FTS search 'AI assistant' ===")
    for e in engine.search_fts("AI assistant"):
        print(e.topic, "→", e.description[:120])

    async def demo_gather():
        await engine.gather_autonomously(
            wikipedia_topics=["Python_(programming_language)"],
            rss_feeds=["https://news.ycombinator.com/rss"],
        )

    asyncio.run(demo_gather())