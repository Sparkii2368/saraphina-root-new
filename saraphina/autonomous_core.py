#!/usr/bin/env python3
"""
Autonomous Core - Saraphina's complete self-awareness and improvement system.

Integrates:
- Universal Search (find anything)
- Self-Documentation (what/why/how tracking)
- Learning Memory (techniques, patterns, lessons)
- Auto-improvement capabilities

Natural Language Interface - No commands needed.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import json


class AutonomousCore:
    """Complete autonomous system with memory and self-improvement."""
    
    def __init__(
        self,
        saraphina_root: Path,
        db,
        knowledge_engine=None,
        self_mod_engine=None
    ):
        """
        Initialize autonomous core.
        
        Args:
            saraphina_root: Root directory
            db: Database connection
            knowledge_engine: Optional KnowledgeEngine
            self_mod_engine: Optional SelfModificationEngine
        """
        self.root = saraphina_root
        self.db = db
        self.knowledge_engine = knowledge_engine
        self.self_mod_engine = self_mod_engine
        
        # Initialize subsystems
        from .universal_search import UniversalSearch
        from .self_documentation import SelfDocumentation
        
        self.search = UniversalSearch(saraphina_root, db, knowledge_engine)
        self.docs = SelfDocumentation(db)
        
        # Auto-document system initialization
        self.docs.document_change(
            what="Autonomous Core Initialized",
            why="Enable complete self-awareness and improvement capabilities",
            how="Integrated UniversalSearch and SelfDocumentation systems",
            phase="Autonomous System",
            techniques=["System Integration", "Natural Language Interface"],
            patterns=["Facade Pattern", "Observer Pattern"],
            lessons=["Unified interface improves usability"],
            can_replicate=True,
            complexity=0.6
        )
    
    def handle_query(self, user_input: str) -> str:
        """
        Handle natural language queries.
        
        Supports:
        - "search for X" - Universal search
        - "how did we do X" - Search modification history
        - "what did I change" - Recent modifications
        - "can you replicate X" - Check if Saraphina can do it
        - "show me lessons learned" - Display lessons
        - "what techniques do you know" - List techniques
        """
        user_input_lower = user_input.lower()
        
        # Search queries
        if any(word in user_input_lower for word in ['search', 'find', 'look for', 'where is']):
            return self._handle_search(user_input)
        
        # Modification history
        if any(phrase in user_input_lower for phrase in ['how did', 'how was', 'how we']):
            return self._handle_how_query(user_input)
        
        # Recent changes
        if any(phrase in user_input_lower for phrase in ['what changed', 'what did', 'recent changes', 'modifications']):
            return self._handle_what_changed(user_input)
        
        # Replication check
        if 'can you' in user_input_lower or 'able to' in user_input_lower:
            return self._handle_capability_query(user_input)
        
        # Lessons learned
        if 'lesson' in user_input_lower or 'learned' in user_input_lower:
            return self._handle_lessons_query()
        
        # Techniques
        if 'technique' in user_input_lower or 'pattern' in user_input_lower:
            return self._handle_techniques_query()
        
        # Summary
        if 'summary' in user_input_lower or 'overview' in user_input_lower:
            return self.docs.generate_summary()
        
        return "I can help you search, review changes, check capabilities, and more. What would you like to know?"
    
    def _handle_search(self, query: str) -> str:
        """Handle search queries."""
        # Remove search keywords to get actual query
        clean_query = query.lower()
        for word in ['search', 'for', 'find', 'look', 'where', 'is']:
            clean_query = clean_query.replace(word, '')
        clean_query = clean_query.strip()
        
        if not clean_query:
            return "What would you like to search for?"
        
        results = self.search.search(clean_query, domains=['all'], limit=10)
        return self.search.format_results(results)
    
    def _handle_how_query(self, query: str) -> str:
        """Handle 'how did we do X' queries."""
        # Extract what they're asking about
        keywords = self.search._extract_keywords(query)
        
        if not keywords:
            return "What would you like to know about?"
        
        # Search modification history
        search_term = ' '.join(keywords)
        results = self.docs.search_history(search_term, limit=3)
        
        if not results:
            return f"I don't have records of how '{search_term}' was done. Try searching for related terms."
        
        output = f"🔍 How '{search_term}' was done:\n\n"
        for entry in results:
            output += self.docs.format_entry(entry)
            output += "\n" + "="*50 + "\n\n"
        
        return output
    
    def _handle_what_changed(self, query: str) -> str:
        """Handle recent changes queries."""
        # Check if asking about specific phase
        import re
        phase_match = re.search(r'phase\s+(\d+)', query.lower())
        
        if phase_match:
            phase_num = phase_match.group(1)
            history = self.docs.get_history(phase=f"Phase {phase_num}", limit=10)
        else:
            history = self.docs.get_history(limit=10)
        
        if not history:
            return "No recent changes found."
        
        output = "📋 Recent Changes:\n\n"
        for entry in history:
            output += f"• [{entry['timestamp'][:19]}] {entry['what']}\n"
            output += f"  Phase: {entry.get('phase', 'unknown')}\n"
            output += f"  Why: {entry['why'][:100]}\n\n"
        
        return output
    
    def _handle_capability_query(self, query: str) -> str:
        """Handle 'can you do X' queries."""
        keywords = self.search._extract_keywords(query)
        
        if not keywords:
            return "What capability are you asking about?"
        
        # Check replicable modifications
        replicable = self.docs.get_replicable_modifications()
        
        # Search for matching capabilities
        search_term = ' '.join(keywords)
        matches = [
            mod for mod in replicable
            if any(kw in mod['what'].lower() or kw in mod['how'].lower() 
                  for kw in keywords)
        ]
        
        if matches:
            output = f"✅ Yes, I can {search_term}. Here's how I've done it before:\n\n"
            for match in matches[:2]:
                output += f"📝 {match['what']}\n"
                output += f"   How: {match['how'][:150]}...\n"
                output += f"   Techniques: {', '.join(match.get('techniques_used', []))}\n\n"
            return output
        else:
            output = f"❌ I don't have experience doing '{search_term}' yet.\n\n"
            output += "However, I can learn! What would you like me to try?"
            return output
    
    def _handle_lessons_query(self) -> str:
        """Handle lessons learned queries."""
        lessons = self.docs.get_lessons_learned()
        
        if not lessons:
            return "No lessons documented yet."
        
        output = "💡 Lessons Learned:\n\n"
        for i, lesson in enumerate(lessons[:10], 1):
            output += f"{i}. {lesson}\n"
        
        if len(lessons) > 10:
            output += f"\n... and {len(lessons) - 10} more lessons"
        
        return output
    
    def _handle_techniques_query(self) -> str:
        """Handle techniques/patterns query."""
        techniques = self.docs.get_techniques_used()
        patterns = self.docs.get_patterns_applied()
        
        output = "🛠️ My Toolbox:\n\n"
        
        if techniques:
            output += "⚡ Techniques Used:\n"
            for tech, count in list(techniques.items())[:10]:
                output += f"  • {tech} ({count}x)\n"
            output += "\n"
        
        if patterns:
            output += "🎯 Design Patterns Applied:\n"
            for pattern, count in list(patterns.items())[:10]:
                output += f"  • {pattern} ({count}x)\n"
        
        return output
    
    def document_current_session(
        self,
        what: str,
        why: str,
        how: str,
        phase: str,
        files_changed: List[str]
    ):
        """
        Document what happened in current session.
        
        Call this after making changes to record them.
        """
        return self.docs.document_change(
            what=what,
            why=why,
            how=how,
            phase=phase,
            files_changed=files_changed,
            can_replicate=True,
            success=True
        )
    
    def can_replicate(self, task_description: str) -> Dict[str, Any]:
        """
        Check if Saraphina can replicate a task.
        
        Returns:
            Dict with can_do, similar_tasks, confidence
        """
        keywords = self.search._extract_keywords(task_description)
        replicable = self.docs.get_replicable_modifications()
        
        similar = [
            mod for mod in replicable
            if any(kw in mod['what'].lower() or kw in mod['how'].lower()
                  for kw in keywords)
        ]
        
        if similar:
            confidence = min(1.0, len(similar) * 0.3)  # More examples = higher confidence
            return {
                'can_do': True,
                'confidence': confidence,
                'similar_tasks': similar[:3],
                'recommendation': 'I have experience with similar tasks'
            }
        else:
            return {
                'can_do': False,
                'confidence': 0.0,
                'similar_tasks': [],
                'recommendation': 'This would be a new capability for me'
            }
    
    def teach_capability(
        self,
        what: str,
        how: str,
        why: str,
        techniques: List[str],
        patterns: List[str],
        lessons: List[str]
    ):
        """
        Teach Saraphina a new capability.
        
        Use this to document how to do something so she can replicate it.
        """
        return self.docs.document_change(
            what=what,
            why=why,
            how=how,
            phase="User Teaching",
            techniques=techniques,
            patterns=patterns,
            lessons=lessons,
            can_replicate=True,
            complexity=0.5
        )
    
    def get_improvement_suggestions(self) -> List[Dict[str, Any]]:
        """
        Get suggestions for self-improvement based on history.
        
        Returns:
            List of suggested improvements Saraphina could make
        """
        suggestions = []
        
        # Analyze what's been done
        techniques = self.docs.get_techniques_used()
        patterns = self.docs.get_patterns_applied()
        
        # Suggest combining successful techniques
        if len(techniques) > 5:
            top_techniques = list(techniques.keys())[:3]
            suggestions.append({
                'type': 'technique_combination',
                'suggestion': f"Combine {', '.join(top_techniques)} for advanced capabilities",
                'confidence': 0.7
            })
        
        # Suggest patterns to learn
        common_patterns = ['Factory', 'Strategy', 'Observer', 'Decorator']
        learned_patterns = set(patterns.keys())
        missing_patterns = [p for p in common_patterns if p not in learned_patterns]
        
        if missing_patterns:
            suggestions.append({
                'type': 'learn_pattern',
                'suggestion': f"Learn {missing_patterns[0]} pattern to expand capabilities",
                'confidence': 0.6
            })
        
        return suggestions
