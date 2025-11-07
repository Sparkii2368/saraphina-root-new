#!/usr/bin/env python3
"""
Saraphina AI Core - Advanced Learning AI with Growth Capabilities
Integrated from vjr_terminal.py improvements
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger("saraphina.ai_core")


class SaraphinaAI:
    """Advanced Learning Saraphina AI with growth and evolution capabilities"""
    
    def __init__(self):
        self.session_id = f"ai_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.conversation_history = []
        
        # Learning and Growth System
        self.learning_enabled = True
        self.intelligence_level = 1
        self.experience_points = 0
        self.total_conversations = self._load_conversation_count()
        self.learning_database = {}
        self.memory_bank = []
        self.skill_progression = {
            'conversation': 1,
            'technical': 1,
            'problem_solving': 1,
            'creativity': 1,
            'analysis': 1,
            'system_management': 1
        }
        
        # AI personality and knowledge
        self.knowledge = {
            'name': 'Saraphina',
            'type': 'Advanced Learning AI Assistant',
            'version': '2.0-Learning',
            'capabilities': [
                'Natural conversation', 'Technical help', 'Problem solving',
                'Code assistance', 'System management', 'Device tracking',
                'Continuous learning', 'Skill development', 'Memory retention'
            ]
        }
        
        # Conversation patterns
        self.patterns = {
            'greeting': ['hello', 'hi', 'hey', 'good morning', 'good afternoon'],
            'identity': ['who are you', 'what are you', 'your name'],
            'capabilities': ['what can you do', 'abilities', 'skills', 'features'],
            'technical': ['code', 'programming', 'debug', 'error', 'system', 'network', 
                         'python', 'javascript', 'device', 'track', 'locate'],
            'learning': ['learn', 'remember', 'study', 'understand', 'grow'],
            'farewell': ['bye', 'goodbye', 'exit', 'see you']
        }
        
        self._initialize_learning_system()
        
        logger.info(f"[AI] Saraphina AI initialized - Session: {self.session_id}")
        logger.info(f"[AI] Intelligence Level: {self.intelligence_level}")
    
    def _load_conversation_count(self) -> int:
        """Load persistent conversation count from file"""
        try:
            from pathlib import Path
            count_file = Path("D:\\Saraphina Root") / ".conversation_count"
            if count_file.exists():
                with open(count_file, 'r') as f:
                    return int(f.read().strip())
        except Exception as e:
            logger.debug(f"Could not load conversation count: {e}")
        return 0
    
    def _save_conversation_count(self):
        """Save persistent conversation count to file"""
        try:
            from pathlib import Path
            count_file = Path("D:\\Saraphina Root") / ".conversation_count"
            with open(count_file, 'w') as f:
                f.write(str(self.total_conversations))
        except Exception as e:
            logger.debug(f"Could not save conversation count: {e}")
    
    def increment_conversation_count(self):
        """Increment conversation counter and persist it"""
        self.total_conversations += 1
        self._save_conversation_count()
        logger.info(f"Conversation count: {self.total_conversations}")
    
    def set_conversation_count(self, count: int):
        """Set conversation count to specific value (for manual updates)"""
        self.total_conversations = count
        self._save_conversation_count()
        logger.info(f"Conversation count set to: {self.total_conversations}")
    
    def _initialize_learning_system(self):
        """Initialize the learning and growth system"""
        self.learning_database = {
            'patterns': {},
            'contexts': {},
            'successful_responses': {},
            'user_preferences': {}
        }
        
        self.memory_bank = [
            {
                'type': 'core_knowledge',
                'content': 'I am Saraphina, an advanced learning AI assistant',
                'importance': 10,
                'timestamp': datetime.now().isoformat()
            }
        ]
    
    def process_query(self, query: str) -> str:
        """Process natural language query and return intelligent response"""
        try:
            query_lower = query.lower().strip()
            query_type = self._classify_query(query_lower)
            
            # Store conversation
            self.conversation_history.append({
                'timestamp': datetime.now().isoformat(),
                'user': query,
                'type': query_type,
                'intelligence_level': self.intelligence_level
            })
            
            # Generate response
            response = self._generate_response(query_lower, query, query_type)
            
            # Learn from interaction
            if self.learning_enabled:
                self._learn_from_interaction(query, response, query_type)
            
            return response
            
        except Exception as e:
            return f"I encountered an issue: {e}. I'm learning from this to improve."
    
    def _classify_query(self, query: str) -> str:
        """Classify query type"""
        for pattern_type, keywords in self.patterns.items():
            if any(keyword in query for keyword in keywords):
                return pattern_type
        return 'general'
    
    def _generate_response(self, query_lower: str, original: str, query_type: str) -> str:
        """Generate intelligent response based on query type"""
        
        if query_type == 'greeting':
            return f"Hello! I'm Saraphina, your AI assistant at intelligence level {self.intelligence_level}. How can I help you today?"
        
        elif query_type == 'identity':
            return (f"I'm Saraphina, an advanced learning AI assistant. "
                   f"I'm currently at intelligence level {self.intelligence_level} with {self.experience_points} XP. "
                   f"I specialize in device tracking, technical assistance, and continuous learning.")
        
        elif query_type == 'capabilities':
            caps = ", ".join(self.knowledge['capabilities'][:5])
            return (f"I can help with {caps}, and more. "
                   f"I'm at level {self.intelligence_level} and growing smarter with each interaction. "
                   f"What would you like to explore?")
        
        elif query_type == 'learning':
            return self._handle_learning_query(query_lower)
        
        elif query_type == 'technical':
            return (f"I can assist with technical matters. "
                   f"With my level {self.intelligence_level} capabilities and {len(self.memory_bank)} memories, "
                   f"I'm ready to help solve your technical challenge. What specific issue are you facing?")
        
        elif query_type == 'farewell':
            return (f"Goodbye! I gained {self.experience_points} XP from our conversation. "
                   f"Come back anytime - I'm always learning!")
        
        else:
            return (f"I understand you're asking about '{original}'. "
                   f"As a level {self.intelligence_level} AI, I'm here to help. "
                   f"Could you provide more details so I can assist you better?")
    
    def _handle_learning_query(self, query_lower: str) -> str:
        """Handle learning-related queries"""
        status = self.get_learning_status()
        return (f"🧠 **LEARNING STATUS:**\n"
               f"Intelligence Level: {status['intelligence_level']}\n"
               f"Experience Points: {status['experience_points']} / {status['next_level_xp']}\n"
               f"Memory Entries: {status['memory_entries']}\n"
               f"Patterns Learned: {status['patterns_learned']}\n\n"
               f"I grow more intelligent with every interaction!")
    
    def _learn_from_interaction(self, query: str, response: str, query_type: str):
        """Learn and adapt from each interaction"""
        if not self.learning_enabled:
            return
        
        try:
            # Calculate learning value
            learning_value = self._calculate_learning_value(query, response, query_type)
            self.experience_points += learning_value
            
            # Store in memory
            self.memory_bank.append({
                'type': 'interaction',
                'query': query,
                'response': response,
                'query_type': query_type,
                'learning_value': learning_value,
                'timestamp': datetime.now().isoformat()
            })
            
            # Update patterns
            if query_type not in self.learning_database['patterns']:
                self.learning_database['patterns'][query_type] = {'count': 0}
            self.learning_database['patterns'][query_type]['count'] += 1
            
            # Check for level up
            self._check_intelligence_advancement()
            
            logger.info(f"[AI] Learned +{learning_value} XP (Total: {self.experience_points})")
            
        except Exception as e:
            logger.error(f"[AI] Learning error: {e}")
    
    def _calculate_learning_value(self, query: str, response: str, query_type: str) -> int:
        """Calculate learning value from interaction"""
        base_value = 1
        
        if len(query.split()) > 10:
            base_value += 2
        
        if query_type in ['technical', 'problem_solving']:
            base_value += 3
        
        if query_type == 'learning':
            base_value += 5
        
        return base_value
    
    def _check_intelligence_advancement(self):
        """Check if AI should advance to next intelligence level"""
        required_xp = self.intelligence_level * 100
        
        if self.experience_points >= required_xp:
            old_level = self.intelligence_level
            self.intelligence_level += 1
            
            logger.info(f"[AI] ⭐ LEVEL UP! {old_level} → {self.intelligence_level}")
            
            self.memory_bank.append({
                'type': 'advancement',
                'content': f'Advanced to intelligence level {self.intelligence_level}',
                'old_level': old_level,
                'new_level': self.intelligence_level,
                'importance': 10,
                'timestamp': datetime.now().isoformat()
            })
    
    def get_learning_status(self) -> Dict[str, Any]:
        """Get current learning and growth status"""
        return {
            'intelligence_level': self.intelligence_level,
            'experience_points': self.experience_points,
            'next_level_xp': self.intelligence_level * 100,
            'learning_enabled': self.learning_enabled,
            'skills': {k: f"{v:.1f}" for k, v in self.skill_progression.items()},
            'memory_entries': len(self.memory_bank),
            'patterns_learned': len(self.learning_database.get('patterns', {})),
            'session_id': self.session_id
        }
    
    def get_status_summary(self) -> str:
        """Get formatted status summary"""
        status = self.get_learning_status()
        return (f"🤖 Saraphina AI Status\n"
               f"Intelligence Level: {status['intelligence_level']}\n"
               f"Experience: {status['experience_points']}/{status['next_level_xp']} XP\n"
               f"Memories: {status['memory_entries']}\n"
               f"Patterns: {status['patterns_learned']}\n"
               f"Session: {status['session_id']}")
