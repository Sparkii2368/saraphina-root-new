#!/usr/bin/env python3
"""
Universal Search System - Search everything Saraphina knows.

Searches:
- Codebase (all Python files)
- Documentation (markdown files)
- Audit logs (code modifications)
- Knowledge base (facts, concepts)
- Modification history (what was done, why)
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
from pathlib import Path
import re
import json
from datetime import datetime


class UniversalSearch:
    """Search across all of Saraphina's knowledge."""
    
    def __init__(self, saraphina_root: Path, db, knowledge_engine=None):
        """
        Initialize universal search.
        
        Args:
            saraphina_root: Root directory of Saraphina
            db: Database connection for audit logs
            knowledge_engine: Optional KnowledgeEngine for semantic search
        """
        self.root = saraphina_root
        self.db = db
        self.knowledge_engine = knowledge_engine
        
        # Search domains
        self.code_dir = self.root / 'saraphina'
        self.docs_dir = self.root / 'docs'
        self.tests_dir = self.root / 'tests'
    
    def search(
        self,
        query: str,
        domains: Optional[List[str]] = None,
        limit: int = 20
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Universal search across all domains.
        
        Args:
            query: Search query (natural language or keywords)
            domains: List of domains to search (code, docs, audit, knowledge, all)
            limit: Max results per domain
        
        Returns:
            Dict with results by domain
        """
        if domains is None or 'all' in domains:
            domains = ['code', 'docs', 'audit', 'knowledge', 'modifications']
        
        results = {}
        
        if 'code' in domains:
            results['code'] = self.search_code(query, limit)
        
        if 'docs' in domains:
            results['docs'] = self.search_docs(query, limit)
        
        if 'audit' in domains:
            results['audit'] = self.search_audit_logs(query, limit)
        
        if 'knowledge' in domains:
            results['knowledge'] = self.search_knowledge(query, limit)
        
        if 'modifications' in domains:
            results['modifications'] = self.search_modifications(query, limit)
        
        return results
    
    def search_code(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search Python code files."""
        results = []
        keywords = self._extract_keywords(query)
        
        # Search all Python files
        for py_file in self.code_dir.rglob('*.py'):
            try:
                content = py_file.read_text(encoding='utf-8')
                
                # Check for keyword matches
                matches = []
                for keyword in keywords:
                    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                    for match in pattern.finditer(content):
                        line_num = content[:match.start()].count('\n') + 1
                        line = content.splitlines()[line_num - 1]
                        matches.append({
                            'line': line_num,
                            'text': line.strip(),
                            'keyword': keyword
                        })
                
                if matches:
                    results.append({
                        'type': 'code',
                        'file': str(py_file.relative_to(self.root)),
                        'matches': matches[:5],  # Top 5 matches per file
                        'relevance': len(matches)
                    })
            
            except Exception:
                pass
        
        # Sort by relevance
        results.sort(key=lambda x: x['relevance'], reverse=True)
        return results[:limit]
    
    def search_docs(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search documentation files."""
        results = []
        keywords = self._extract_keywords(query)
        
        # Search markdown files
        for doc_file in self.docs_dir.rglob('*.md'):
            try:
                content = doc_file.read_text(encoding='utf-8')
                
                # Check for matches
                matches = []
                for keyword in keywords:
                    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                    for match in pattern.finditer(content):
                        line_num = content[:match.start()].count('\n') + 1
                        line = content.splitlines()[line_num - 1]
                        matches.append({
                            'line': line_num,
                            'text': line.strip(),
                            'keyword': keyword
                        })
                
                if matches:
                    results.append({
                        'type': 'documentation',
                        'file': str(doc_file.relative_to(self.root)),
                        'matches': matches[:3],
                        'relevance': len(matches)
                    })
            
            except Exception:
                pass
        
        results.sort(key=lambda x: x['relevance'], reverse=True)
        return results[:limit]
    
    def search_audit_logs(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search code modification audit logs."""
        results = []
        keywords = self._extract_keywords(query)
        
        try:
            # Search code_audit_logs table
            keyword_conditions = ' OR '.join([
                f"file_path LIKE '%{kw}%' OR action LIKE '%{kw}%' OR details LIKE '%{kw}%'"
                for kw in keywords
            ])
            
            query_sql = f"""
                SELECT * FROM code_audit_logs
                WHERE {keyword_conditions}
                ORDER BY timestamp DESC
                LIMIT ?
            """
            
            rows = self.db.execute(query_sql, (limit,)).fetchall()
            
            for row in rows:
                entry = dict(row)
                if entry['details']:
                    entry['details'] = json.loads(entry['details'])
                
                results.append({
                    'type': 'audit_log',
                    'timestamp': entry['timestamp'],
                    'action': entry['action'],
                    'file': entry['file_path'],
                    'risk_level': entry.get('risk_level'),
                    'success': entry['success'],
                    'details': entry.get('details', {})
                })
        
        except Exception as e:
            # Table might not exist yet
            pass
        
        return results
    
    def search_knowledge(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search knowledge base (if available)."""
        results = []
        
        if self.knowledge_engine:
            try:
                # Use knowledge engine's search
                facts = self.knowledge_engine.recall(query, limit=limit)
                
                for fact in facts:
                    results.append({
                        'type': 'knowledge',
                        'fact': fact.get('content', ''),
                        'confidence': fact.get('confidence', 0.0),
                        'source': fact.get('source', 'unknown'),
                        'created': fact.get('created_at', '')
                    })
            
            except Exception:
                pass
        
        return results
    
    def search_modifications(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search self-modification history."""
        results = []
        keywords = self._extract_keywords(query)
        
        try:
            # Search modification_history table (if exists)
            keyword_conditions = ' OR '.join([
                f"what LIKE '%{kw}%' OR why LIKE '%{kw}%' OR how LIKE '%{kw}%'"
                for kw in keywords
            ])
            
            query_sql = f"""
                SELECT * FROM modification_history
                WHERE {keyword_conditions}
                ORDER BY timestamp DESC
                LIMIT ?
            """
            
            rows = self.db.execute(query_sql, (limit,)).fetchall()
            
            for row in rows:
                results.append({
                    'type': 'modification',
                    'timestamp': row['timestamp'],
                    'what': row['what'],
                    'why': row['why'],
                    'how': row['how'],
                    'phase': row.get('phase', 'unknown'),
                    'files_changed': row.get('files_changed', '')
                })
        
        except Exception:
            # Table might not exist yet
            pass
        
        return results
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract keywords from natural language query."""
        # Remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                     'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
                     'how', 'what', 'where', 'when', 'why', 'who', 'which', 'this', 'that',
                     'can', 'could', 'should', 'would', 'do', 'does', 'did', 'i', 'me', 'my'}
        
        words = re.findall(r'\w+', query.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        return keywords
    
    def format_results(self, results: Dict[str, List[Dict[str, Any]]]) -> str:
        """Format search results as readable text."""
        if not any(results.values()):
            return "No results found."
        
        output = "🔍 Search Results\n\n"
        
        # Code results
        if results.get('code'):
            output += "📝 Code:\n"
            for result in results['code'][:5]:
                output += f"  • {result['file']} ({result['relevance']} matches)\n"
                for match in result['matches'][:2]:
                    output += f"    Line {match['line']}: {match['text'][:80]}\n"
            output += "\n"
        
        # Documentation results
        if results.get('docs'):
            output += "📚 Documentation:\n"
            for result in results['docs'][:5]:
                output += f"  • {result['file']}\n"
                for match in result['matches'][:1]:
                    output += f"    {match['text'][:80]}\n"
            output += "\n"
        
        # Audit logs
        if results.get('audit'):
            output += "📜 Audit Logs:\n"
            for result in results['audit'][:3]:
                status = "✅" if result['success'] else "❌"
                output += f"  {status} [{result['timestamp'][:19]}] {result['action']}\n"
                output += f"     File: {result['file']}\n"
            output += "\n"
        
        # Knowledge
        if results.get('knowledge'):
            output += "🧠 Knowledge Base:\n"
            for result in results['knowledge'][:3]:
                output += f"  • {result['fact'][:100]}\n"
                output += f"    (Confidence: {result['confidence']:.1%})\n"
            output += "\n"
        
        # Modifications
        if results.get('modifications'):
            output += "🔧 Modifications:\n"
            for result in results['modifications'][:3]:
                output += f"  • [{result['timestamp'][:19]}] {result['what']}\n"
                output += f"    Why: {result['why'][:80]}\n"
            output += "\n"
        
        return output
