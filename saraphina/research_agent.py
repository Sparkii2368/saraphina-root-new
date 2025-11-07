#!/usr/bin/env python3
"""
ResearchAgent - autonomous knowledge gathering with GPT-4 recursive querying.
Sources:
- KnowledgeEngine recall
- Local repository search (docs, README, code headers)
- GPT-4 API for structured research (if API key available)
- Optional web fetch (disabled unless preference 'web_research_enabled' == 'true')

Capabilities:
- Recursive query expansion
- Multi-source synthesis
- Provenance tracking
- Natural language interface
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
import os
import re
import json

from .db import write_audit_log, get_preference

class ResearchAgent:
    def __init__(self, ke):
        self.ke = ke  # KnowledgeEngine instance
        self.conn = ke.conn
        self._check_gpt4_available()

    def _check_gpt4_available(self):
        """Check if GPT-4 API is available."""
        self.gpt4_available = False
        try:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                from openai import OpenAI
                self.gpt4_available = True
        except Exception:
            pass
    
    def _gpt4_research(self, topic: str, depth: int = 2) -> Dict[str, Any]:
        """Use GPT-4 for structured research with recursive querying."""
        if not self.gpt4_available:
            return {'facts': [], 'subtopics': [], 'error': 'GPT-4 not available'}
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            # Initial research query
            prompt = f"""Research the topic: {topic}

Provide a structured response with:
1. 10 canonical facts about this topic (numbered list)
2. 3-5 subtopics for deeper exploration
3. Key relationships and connections

Format your response as:
FACTS:
1. [fact]
2. [fact]
...

SUBTOPICS:
- [subtopic]
- [subtopic]
...

CONNECTIONS:
[relationships between concepts]
"""
            
            response = client.chat.completions.create(
                model="gpt-4o",  # Latest GPT-4o model with enhanced reasoning
                messages=[
                    {"role": "system", "content": "You are a research assistant that provides accurate, structured information with deep analysis."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2500
            )
            
            content = response.choices[0].message.content or ""
            
            # Parse structured response
            facts = []
            subtopics = []
            connections = ""
            
            # Extract facts
            facts_match = re.search(r'FACTS?:(.+?)(?:SUBTOPICS?:|$)', content, re.DOTALL)
            if facts_match:
                facts_text = facts_match.group(1)
                facts = [f.strip() for f in re.findall(r'\d+\.\s*(.+)', facts_text) if f.strip()]
            
            # Extract subtopics
            subtopics_match = re.search(r'SUBTOPICS?:(.+?)(?:CONNECTIONS?:|$)', content, re.DOTALL)
            if subtopics_match:
                subtopics_text = subtopics_match.group(1)
                subtopics = [s.strip() for s in re.findall(r'-\s*(.+)', subtopics_text) if s.strip()]
            
            # Extract connections
            conn_match = re.search(r'CONNECTIONS?:(.+?)$', content, re.DOTALL)
            if conn_match:
                connections = conn_match.group(1).strip()
            
            # Recursive research on subtopics if depth > 1
            subtopic_research = {}
            if depth > 1 and subtopics:
                for st in subtopics[:3]:  # Limit to 3 subtopics
                    subtopic_research[st] = self._gpt4_research(st, depth=depth-1)
            
            return {
                'facts': facts,
                'subtopics': subtopics,
                'connections': connections,
                'subtopic_research': subtopic_research,
                'raw_response': content
            }
            
        except Exception as e:
            return {'facts': [], 'subtopics': [], 'error': str(e)}
    
    def _local_search(self, topic: str, max_hits: int = 10) -> List[Dict[str, Any]]:
        roots = ['.', 'docs', 'README.md', 'saraphina']
        words = [w for w in re.findall(r"[A-Za-z0-9_#+.-]+", topic) if len(w) >= 3]
        results: List[Dict[str, Any]] = []
        try:
            for root in roots:
                if os.path.isdir(root):
                    for dirpath, _, filenames in os.walk(root):
                        if len(results) >= max_hits:
                            break
                        # Skip venv/node_modules/cache
                        if any(x in dirpath for x in ['.git','node_modules','.venv','__pycache__','ai_data']):
                            continue
                        for fn in filenames:
                            if not fn.lower().endswith(('.md','.txt','.py','.ts','.json','.rst')):
                                continue
                            fpath = os.path.join(dirpath, fn)
                            try:
                                with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                                    txt = f.read()
                                if any(w.lower() in txt.lower() for w in words):
                                    snippet = txt[:4000]
                                    results.append({'path': fpath, 'snippet': snippet})
                                    if len(results) >= max_hits:
                                        break
                            except Exception:
                                continue
                elif os.path.isfile(root):
                    try:
                        with open(root, 'r', encoding='utf-8', errors='ignore') as f:
                            txt = f.read()
                        if any(w.lower() in txt.lower() for w in words):
                            results.append({'path': root, 'snippet': txt[:4000]})
                    except Exception:
                        pass
        except Exception:
            pass
        return results[:max_hits]

    def _web_fetch(self, topic: str, max_hits: int = 3) -> List[Dict[str, Any]]:
        # Disabled by default — controlled by preference 'web_research_enabled'
        try:
            from .db import get_preference
            enabled = (get_preference(self.conn, 'web_research_enabled') == 'true')
        except Exception:
            enabled = False
        if not enabled:
            return []
        try:
            import requests
        except Exception:
            return []
        # naive: query a small curated set if allowed (placeholder)
        sources: List[str] = []
        # Read whitelist from prefs
        wl = get_preference(self.conn, 'web_research_whitelist')
        allowed = json.loads(wl) if wl else ['https://docs.python.org/3/', 'https://en.wikipedia.org/wiki/']
        for base in allowed:
            try:
                r = requests.get(base, timeout=5)
                if r.ok:
                    txt = r.text
                    if topic.lower() in txt.lower():
                        # crude text extraction
                        body = re.sub('<[^<]+?>', ' ', txt)
                        sources.append(body[:8000])
                if len(sources) >= max_hits:
                    break
            except Exception:
                continue
        return [{'url': allowed[0], 'text': s} for s in sources]

    @staticmethod
    def _summarize(chunks: List[str], topic: str, max_len: int = 8) -> str:
        # Simple extractive: pick sentences mentioning the topic or key terms
        sent_re = re.compile(r"(?<=[.!?])\s+")
        scores: List[tuple] = []
        keys = [w.lower() for w in re.findall(r"[A-Za-z0-9_#+.-]+", topic) if len(w) >= 4]
        for ch in chunks:
            for s in sent_re.split(ch.replace('\n',' ')):
                t = s.strip()
                if not t:
                    continue
                score = sum(1 for k in keys if k in t.lower()) + min(2, len(t)//80)
                scores.append((score, t[:240]))
        scores.sort(key=lambda x: x[0], reverse=True)
        top = [t for _, t in scores[:max_len]]
        return "\n- ".join(top) if top else "No concise summary available yet."

    def research(self, topic: str, allow_web: Optional[bool] = None, max_sources: int = 5, 
                use_gpt4: bool = True, recursive_depth: int = 1, store_facts: bool = True) -> Dict[str, Any]:
        """
        Comprehensive research using multiple sources.
        
        Args:
            topic: Research topic
            allow_web: Enable web search
            max_sources: Max sources per type
            use_gpt4: Use GPT-4 for structured research
            recursive_depth: Depth of recursive GPT-4 queries (1-3)
            store_facts: Automatically store discovered facts in KB
        """
        # Gather from multiple sources
        kb_hits = self.ke.recall(topic, top_k=max_sources, threshold=0.5)
        local = self._local_search(topic, max_hits=max_sources)
        web = self._web_fetch(topic, max_hits=max_sources) if (allow_web or False) else []
        
        # GPT-4 research (if available and enabled)
        gpt4_result = {}
        if use_gpt4 and self.gpt4_available:
            gpt4_result = self._gpt4_research(topic, depth=recursive_depth)
        
        # Assemble content
        chunks: List[str] = []
        sources_desc: List[Dict[str, Any]] = []
        
        for h in kb_hits:
            text = (h.get('summary') or '') + ' ' + (h.get('content') or '')
            chunks.append(text)
            sources_desc.append({'type': 'kb', 'id': h.get('id'), 'topic': h.get('topic')})
        
        for l in local:
            chunks.append(l.get('snippet') or '')
            sources_desc.append({'type': 'file', 'path': l.get('path')})
        
        for w in web:
            chunks.append(w.get('text') or '')
            sources_desc.append({'type': 'web', 'url': w.get('url')})
        
        # Add GPT-4 facts as sources
        if gpt4_result.get('facts'):
            chunks.extend(gpt4_result['facts'])
            sources_desc.append({'type': 'gpt4', 'model': 'gpt-4', 'facts_count': len(gpt4_result['facts'])})
        
        # Summarize
        summary = self._summarize(chunks, topic, max_len=10)
        content = "\n\n".join(chunks[:20])
        
        rid = __import__('uuid').uuid4().hex
        now = datetime.utcnow().isoformat()
        
        # Store facts in knowledge base
        stored_fact_ids = []
        if store_facts and gpt4_result.get('facts'):
            for i, fact in enumerate(gpt4_result['facts'][:10], 1):
                try:
                    fid = self.ke.store_fact(
                        topic=topic.lower(),
                        summary=f"{topic}: {fact[:60]}",
                        content=fact,
                        source='gpt4_research',
                        confidence=0.85
                    )
                    stored_fact_ids.append(fid)
                except Exception:
                    pass
        
        # Store research report
        try:
            cur = self.conn.cursor()
            cur.execute(
                "INSERT INTO research_reports (id, topic, summary, content, sources, created_at) VALUES (?,?,?,?,?,?)",
                (rid, topic, summary, content, json.dumps(sources_desc, ensure_ascii=False), now)
            )
            self.conn.commit()
            write_audit_log(self.conn, actor='research', action='create_report', target=rid, 
                          details={'topic': topic, 'facts_stored': len(stored_fact_ids)})
        except Exception:
            pass
        
        return {
            'id': rid,
            'topic': topic,
            'summary': summary,
            'sources': sources_desc,
            'created_at': now,
            'gpt4_facts': gpt4_result.get('facts', []),
            'subtopics': gpt4_result.get('subtopics', []),
            'connections': gpt4_result.get('connections', ''),
            'stored_fact_ids': stored_fact_ids,
            'fact_count': len(stored_fact_ids),
        }
