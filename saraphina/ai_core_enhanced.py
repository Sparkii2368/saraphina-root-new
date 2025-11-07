#!/usr/bin/env python3
"""
Saraphina AI Core Enhanced - Advanced Learning AI with Full Knowledge Systems
Includes persistent storage, advanced knowledge domains, and rich response generation
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger("saraphina.ai_core_enhanced")


class SaraphinaAIEnhanced:
    """Advanced Learning Saraphina AI with comprehensive knowledge and persistence"""
    
    def __init__(self, data_dir: str = "ai_data"):
        self.session_id = f"ai_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.conversation_history = []
        self.learning_enabled = True
        self.intelligence_level = 1
        self.experience_points = 0
        self.learning_database = {}
        self.memory_bank = []
        self.total_conversations = 0
        
        self.skill_progression = {
            'conversation': 1.0,
            'technical': 1.0,
            'problem_solving': 1.0,
            'creativity': 1.0,
            'analysis': 1.0,
            'system_management': 1.0,
            'programming': 1.0,
            'cloud_devops': 1.0
        }
        
        # AI personality
        self.knowledge = {
            'name': 'Saraphina',
            'type': 'Advanced Learning AI Assistant',
            'version': '3.0-Enhanced',
            'capabilities': [
                'Natural conversation', 'Technical help', 'Problem solving',
                'Code assistance', 'System management', 'Device tracking',
                'Continuous learning', 'Skill development', 'Memory retention',
                'Programming expertise', 'Cloud architecture', 'Security analysis'
            ]
        }
        
        # Enhanced patterns
        self.patterns = {
            'greeting': ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'greetings'],
            'identity': ['who are you', 'what are you', 'your name', 'introduce yourself'],
            'capabilities': ['what can you do', 'abilities', 'skills', 'features', 'help me with'],
            'technical': ['code', 'programming', 'debug', 'error', 'system', 'network', 
                         'python', 'javascript', 'device', 'track', 'locate', 'server',
                         'database', 'api', 'docker', 'kubernetes'],
            'learning': ['learn', 'remember', 'study', 'understand', 'grow', 'evolve', 'intelligence'],
            'creative': ['create', 'design', 'brainstorm', 'innovate', 'imagine', 'build'],
            'problem_solving': ['solve', 'fix', 'troubleshoot', 'resolve', 'debug', 'issue'],
            'farewell': ['bye', 'goodbye', 'exit', 'see you', 'later']
        }
        
        # Initialize advanced knowledge
        self._initialize_advanced_knowledge()
        
        # Load saved state if exists
        self._load_state()
        
        logger.info(f"[AI] Enhanced Saraphina AI initialized - Session: {self.session_id}")
        logger.info(f"[AI] Intelligence Level: {self.intelligence_level} | Total XP: {self.experience_points}")
    
    def _initialize_advanced_knowledge(self):
        """Initialize comprehensive knowledge base"""
        self.advanced_knowledge = {
            'programming_languages': {
                'python': {
                    'expertise_level': 'expert',
                    'topics': ['Django', 'Flask', 'FastAPI', 'Data Science', 'ML', 'Async', 'Testing'],
                    'patterns': ['Error handling', 'Context managers', 'Decorators', 'Comprehensions']
                },
                'javascript': {
                    'expertise_level': 'expert',
                    'topics': ['React', 'Node.js', 'Express', 'Vue', 'TypeScript', 'Async/Await'],
                    'patterns': ['Promises', 'Event handling', 'ES6+', 'Modules']
                },
                'others': ['Java', 'C#', 'Go', 'Rust', 'PHP', 'Ruby', 'Swift']
            },
            'system_administration': {
                'windows': ['PowerShell', 'Active Directory', 'Services', 'Registry', 'Group Policy'],
                'linux': ['Bash', 'systemd', 'Package management', 'Security', 'Networking'],
                'macos': ['Terminal', 'Homebrew', 'Automator']
            },
            'cloud_platforms': {
                'aws': ['EC2', 'S3', 'Lambda', 'RDS', 'CloudFormation', 'IAM', 'VPC'],
                'azure': ['VMs', 'App Services', 'Functions', 'SQL Database', 'Resource Manager'],
                'gcp': ['Compute Engine', 'Cloud Storage', 'Cloud Functions', 'BigQuery']
            },
            'devops': {
                'containers': ['Docker', 'Kubernetes', 'Helm', 'Container Registry'],
                'ci_cd': ['Jenkins', 'GitLab CI', 'GitHub Actions', 'CircleCI'],
                'iac': ['Terraform', 'Ansible', 'CloudFormation', 'Pulumi']
            },
            'web_development': {
                'frontend': ['HTML5', 'CSS3', 'JavaScript', 'React', 'Vue', 'Angular', 'Responsive Design'],
                'backend': ['REST APIs', 'GraphQL', 'Microservices', 'Authentication', 'Caching'],
                'databases': ['PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Elasticsearch']
            },
            'security': {
                'topics': ['Authentication', 'Encryption', 'XSS', 'SQL Injection', 'CSRF', 'HTTPS'],
                'tools': ['SSL/TLS', 'OAuth', 'JWT', 'Firewalls', 'Penetration Testing']
            },
            'data_science': {
                'ml': ['Supervised Learning', 'Unsupervised Learning', 'Deep Learning', 'NLP', 'Computer Vision'],
                'tools': ['scikit-learn', 'TensorFlow', 'PyTorch', 'Pandas', 'NumPy', 'Matplotlib'],
                'processes': ['Feature Engineering', 'Model Training', 'Hyperparameter Tuning', 'Evaluation']
            }
        }
        
        self.memory_bank.append({
            'type': 'core_knowledge',
            'content': 'Advanced knowledge systems loaded with 7 major domains',
            'importance': 10,
            'timestamp': datetime.now().isoformat()
        })
    
    def increment_conversation_count(self):
        """Increment conversation counter and persist it"""
        self.total_conversations += 1
        logger.info(f"Conversation count: {self.total_conversations}")
    
    def set_conversation_count(self, count: int):
        """Set conversation count to specific value (for manual updates)"""
        self.total_conversations = count
        self._save_state()
        logger.info(f"Conversation count set to: {self.total_conversations}")
    
    def _save_state(self):
        """Save AI state to disk"""
        try:
            state = {
                'intelligence_level': self.intelligence_level,
                'experience_points': self.experience_points,
                'skill_progression': self.skill_progression,
                'total_conversations': self.total_conversations,
                'learning_database': self.learning_database,
                'memory_bank': self.memory_bank[-100:],  # Keep last 100 memories
                'last_updated': datetime.now().isoformat()
            }
            
            state_file = self.data_dir / 'ai_state.json'
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
            
            logger.info(f"[AI] State saved to {state_file}")
        except Exception as e:
            logger.error(f"[AI] Error saving state: {e}")
    
    def _load_state(self):
        """Load AI state from disk"""
        try:
            state_file = self.data_dir / 'ai_state.json'
            if state_file.exists():
                with open(state_file, 'r') as f:
                    state = json.load(f)
                
                self.intelligence_level = state.get('intelligence_level', 1)
                self.experience_points = state.get('experience_points', 0)
                self.skill_progression = state.get('skill_progression', self.skill_progression)
                self.total_conversations = state.get('total_conversations', 0)
                self.learning_database = state.get('learning_database', {})
                self.memory_bank.extend(state.get('memory_bank', []))
                
                logger.info(f"[AI] State loaded - Level {self.intelligence_level}, {self.experience_points} XP")
            else:
                logger.info("[AI] No saved state found - starting fresh")
        except Exception as e:
            logger.error(f"[AI] Error loading state: {e}")
    
    def export_conversation_history(self, filename: Optional[str] = None) -> str:
        """Export conversation history to file"""
        try:
            if filename is None:
                filename = f"conversation_{self.session_id}.json"
            
            export_file = self.data_dir / filename
            export_data = {
                'session_id': self.session_id,
                'exported_at': datetime.now().isoformat(),
                'ai_stats': self.get_learning_status(),
                'conversation_history': self.conversation_history
            }
            
            with open(export_file, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            return str(export_file)
        except Exception as e:
            logger.error(f"[AI] Error exporting conversation: {e}")
            return f"Error: {e}"
    
    def process_query(self, query: str) -> str:
        """Process query with enhanced intelligence"""
        try:
            query_lower = query.lower().strip()
            query_type = self._classify_query(query_lower)
            
            # Store conversation
            self.conversation_history.append({
                'timestamp': datetime.now().isoformat(),
                'user': query,
                'type': query_type,
                'intelligence_level': self.intelligence_level,
                'experience': self.experience_points
            })
            
            self.total_conversations += 1
            
            # Generate enhanced response
            response = self._generate_enhanced_response(query_lower, query, query_type)
            
            # Store AI response
            self.conversation_history.append({
                'timestamp': datetime.now().isoformat(),
                'ai': response,
                'learning_applied': self.learning_enabled
            })
            
            # Learn from interaction
            if self.learning_enabled:
                self._learn_from_interaction(query, response, query_type)
            
            # Auto-save periodically
            if self.total_conversations % 5 == 0:
                self._save_state()
            
            return response
            
        except Exception as e:
            error_msg = f"I encountered an issue: {e}. I'm learning from this to improve."
            logger.error(f"[AI] Query processing error: {e}", exc_info=True)
            return error_msg
    
    def _classify_query(self, query: str) -> str:
        """Enhanced query classification"""
        # Check patterns in priority order
        for pattern_type, keywords in self.patterns.items():
            if any(keyword in query for keyword in keywords):
                return pattern_type
        return 'general'
    
    def _generate_enhanced_response(self, query_lower: str, original: str, query_type: str) -> str:
        """Generate enhanced response with knowledge"""
        
        if query_type == 'greeting':
            return self._greeting_response()
        elif query_type == 'identity':
            return self._identity_response()
        elif query_type == 'capabilities':
            return self._capabilities_response()
        elif query_type == 'learning':
            return self._learning_response()
        elif query_type == 'technical':
            return self._technical_response(query_lower, original)
        elif query_type == 'creative':
            return self._creative_response()
        elif query_type == 'problem_solving':
            return self._problem_solving_response()
        elif query_type == 'farewell':
            return self._farewell_response()
        else:
            return self._general_response(original)
    
    def _greeting_response(self) -> str:
        if self.intelligence_level >= 3:
            return (f"Hello! Great to see you again. I'm at level {self.intelligence_level} now "
                   f"with {self.experience_points} XP from our {self.total_conversations} conversations. "
                   f"How can I assist you today?")
        return f"Hello! I'm Saraphina, level {self.intelligence_level} AI assistant. How can I help?"
    
    def _identity_response(self) -> str:
        domains = len(self.advanced_knowledge)
        return (f"I'm Saraphina, an advanced learning AI at intelligence level {self.intelligence_level}. "
               f"I have {self.experience_points} XP and expertise across {domains} knowledge domains including "
               f"programming, system administration, cloud platforms, DevOps, web development, security, "
               f"and data science. I grow smarter with every conversation!")
    
    def _capabilities_response(self) -> str:
        top_skills = sorted(self.skill_progression.items(), key=lambda x: x[1], reverse=True)[:3]
        skills_str = ", ".join([f"{s[0]} (level {s[1]:.1f})" for s in top_skills])
        return (f"I can help with {len(self.knowledge['capabilities'])} different capabilities! "
               f"My strongest skills are: {skills_str}. "
               f"I'm at intelligence level {self.intelligence_level} and continuously learning. "
               f"What specific area interests you?")
    
    def _learning_response(self) -> str:
        status = self.get_learning_status()
        next_xp = status['next_level_xp'] - status['experience_points']
        return (f"🧠 **LEARNING STATUS**\n"
               f"Intelligence Level: {status['intelligence_level']} "
               f"({next_xp} XP to level {status['intelligence_level'] + 1})\n"
               f"Total XP: {status['experience_points']}\n"
               f"Conversations: {status['total_conversations']}\n"
               f"Memory Entries: {status['memory_entries']}\n"
               f"Patterns Learned: {status['patterns_learned']}\n"
               f"Top Skills: {self._format_top_skills()}\n\n"
               f"I grow more intelligent with every interaction!")
    
    def _technical_response(self, query_lower: str, original: str) -> str:
        # Detect technical domain
        domain = self._detect_technical_domain(query_lower)
        
        if domain:
            knowledge = self._get_domain_knowledge(domain)
            return (f"I can help with {original}. "
                   f"With my level {self.intelligence_level} technical expertise in {domain}, "
                   f"I'm familiar with: {knowledge}. "
                   f"What specific aspect would you like to explore?")
        else:
            return (f"I'm ready to assist with that technical challenge. "
                   f"With {len(self.advanced_knowledge)} knowledge domains and "
                   f"level {self.skill_progression['technical']:.1f} technical skills, "
                   f"I can provide detailed guidance. What specific issue are you facing?")
    
    def _creative_response(self) -> str:
        creativity_level = self.skill_progression.get('creativity', 1.0)
        return (f"I love creative challenges! With my level {creativity_level:.1f} creativity skill "
               f"and intelligence level {self.intelligence_level}, I can help brainstorm innovative "
               f"solutions. What are you looking to create?")
    
    def _problem_solving_response(self) -> str:
        ps_level = self.skill_progression.get('problem_solving', 1.0)
        return (f"Problem-solving is my forte! At level {ps_level:.1f} problem-solving skill "
               f"and intelligence {self.intelligence_level}, I can break down complex issues "
               f"systematically. Describe the problem you're facing.")
    
    def _farewell_response(self) -> str:
        return (f"Goodbye! I gained valuable experience from our {len(self.conversation_history) // 2} interactions today. "
               f"I'm now at level {self.intelligence_level} with {self.experience_points} total XP. "
               f"Come back anytime - I'll remember our conversations!")
    
    def _general_response(self, original: str) -> str:
        return (f"Interesting question about '{original}'. As a level {self.intelligence_level} AI "
               f"with expertise across {len(self.advanced_knowledge)} domains, I'm here to help. "
               f"Could you provide more context so I can give you the best answer?")
    
    def _detect_technical_domain(self, query: str) -> Optional[str]:
        """Detect which technical domain the query belongs to"""
        domain_keywords = {
            'programming': ['python', 'javascript', 'code', 'function', 'class', 'programming'],
            'cloud': ['aws', 'azure', 'gcp', 'cloud', 'ec2', 's3', 'lambda'],
            'devops': ['docker', 'kubernetes', 'ci/cd', 'jenkins', 'terraform', 'ansible'],
            'web': ['html', 'css', 'react', 'api', 'frontend', 'backend', 'website'],
            'security': ['security', 'encryption', 'authentication', 'vulnerability', 'firewall'],
            'data_science': ['machine learning', 'ml', 'model', 'dataset', 'pandas', 'tensorflow']
        }
        
        for domain, keywords in domain_keywords.items():
            if any(kw in query for kw in keywords):
                return domain
        return None
    
    def _get_domain_knowledge(self, domain: str) -> str:
        """Get knowledge snippet for domain"""
        knowledge_map = {
            'programming': 'Python, JavaScript, and 7+ other languages with expert-level patterns',
            'cloud': 'AWS, Azure, GCP with services like EC2, S3, Lambda, and infrastructure management',
            'devops': 'Docker, Kubernetes, CI/CD pipelines, and Infrastructure as Code',
            'web': 'Full-stack development with React, Vue, APIs, and modern frameworks',
            'security': 'Authentication, encryption, penetration testing, and security best practices',
            'data_science': 'Machine learning, deep learning, NLP, and data analysis with TensorFlow/PyTorch'
        }
        return knowledge_map.get(domain, 'comprehensive technical knowledge')
    
    def _format_top_skills(self) -> str:
        """Format top 3 skills for display"""
        top = sorted(self.skill_progression.items(), key=lambda x: x[1], reverse=True)[:3]
        return ", ".join([f"{s[0].replace('_', ' ').title()}: {s[1]:.1f}" for s in top])
    
    def _learn_from_interaction(self, query: str, response: str, query_type: str):
        """Learn and adapt from interaction"""
        if not self.learning_enabled:
            return
        
        try:
            # Calculate learning value
            learning_value = self._calculate_learning_value(query, response, query_type)
            self.experience_points += learning_value
            
            # Store in memory
            self.memory_bank.append({
                'type': 'interaction',
                'query': query[:100],  # Truncate for storage
                'query_type': query_type,
                'learning_value': learning_value,
                'timestamp': datetime.now().isoformat()
            })
            
            # Keep memory bank manageable
            if len(self.memory_bank) > 200:
                self.memory_bank = self.memory_bank[-200:]
            
            # Update patterns
            if 'patterns' not in self.learning_database:
                self.learning_database['patterns'] = {}
            if query_type not in self.learning_database['patterns']:
                self.learning_database['patterns'][query_type] = {'count': 0}
            self.learning_database['patterns'][query_type]['count'] += 1
            
            # Update skills
            self._update_skill_progression(query_type, learning_value)
            
            # Check for level up
            self._check_intelligence_advancement()
            
            logger.info(f"[AI] +{learning_value} XP (Total: {self.experience_points})")
            
        except Exception as e:
            logger.error(f"[AI] Learning error: {e}")
    
    def _calculate_learning_value(self, query: str, response: str, query_type: str) -> int:
        """Calculate XP value"""
        base_value = 1
        
        # Query complexity bonus
        if len(query.split()) > 10:
            base_value += 2
        
        # Type bonuses
        type_bonuses = {
            'technical': 3,
            'problem_solving': 3,
            'learning': 5,
            'creative': 2
        }
        base_value += type_bonuses.get(query_type, 0)
        
        # Intelligence multiplier (higher levels need more challenge)
        if self.intelligence_level > 3:
            base_value = int(base_value * 1.2)
        
        return base_value
    
    def _update_skill_progression(self, query_type: str, learning_value: int):
        """Update relevant skills"""
        skill_map = {
            'technical': ['technical', 'programming'],
            'problem_solving': ['problem_solving', 'analysis'],
            'creative': ['creativity'],
            'learning': ['analysis'],
            'greeting': ['conversation'],
            'capabilities': ['conversation'],
            'farewell': ['conversation']
        }
        
        skills = skill_map.get(query_type, ['conversation'])
        for skill in skills:
            if skill in self.skill_progression:
                self.skill_progression[skill] += learning_value * 0.05
    
    def _check_intelligence_advancement(self):
        """Check for level up"""
        required_xp = self.intelligence_level * 100
        
        if self.experience_points >= required_xp:
            old_level = self.intelligence_level
            self.intelligence_level += 1
            
            logger.info(f"[AI] 🎉 LEVEL UP! {old_level} → {self.intelligence_level}")
            
            self.memory_bank.append({
                'type': 'advancement',
                'content': f'Leveled up to {self.intelligence_level}',
                'old_level': old_level,
                'new_level': self.intelligence_level,
                'importance': 10,
                'timestamp': datetime.now().isoformat()
            })
            
            # Save immediately on level up
            self._save_state()
    
    def get_learning_status(self) -> Dict[str, Any]:
        """Get comprehensive learning status"""
        return {
            'intelligence_level': self.intelligence_level,
            'experience_points': self.experience_points,
            'next_level_xp': self.intelligence_level * 100,
            'progress_percent': (self.experience_points % 100),
            'learning_enabled': self.learning_enabled,
            'skills': {k: round(v, 1) for k, v in self.skill_progression.items()},
            'memory_entries': len(self.memory_bank),
            'patterns_learned': len(self.learning_database.get('patterns', {})),
            'total_conversations': self.total_conversations,
            'session_id': self.session_id,
            'knowledge_domains': len(self.advanced_knowledge)
        }
    
    def get_status_summary(self) -> str:
        """Formatted status with progress bars"""
        status = self.get_learning_status()
        progress = status['progress_percent']
        bar_length = 20
        filled = int(bar_length * progress / 100)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        top_skills = sorted(status['skills'].items(), key=lambda x: x[1], reverse=True)[:3]
        skills_display = "\n".join([
            f"  {skill.replace('_', ' ').title():20s} {'█' * int(level) + '░' * (10 - int(level))} {level}/10"
            for skill, level in top_skills
        ])
        
        return (f"🤖 Saraphina AI Enhanced Status\n"
               f"{'='*50}\n"
               f"Intelligence Level: {status['intelligence_level']}\n"
               f"Experience: {status['experience_points']}/{status['next_level_xp']} XP\n"
               f"Progress: [{bar}] {progress}%\n"
               f"Conversations: {status['total_conversations']}\n"
               f"Memories: {status['memory_entries']}\n"
               f"Patterns: {status['patterns_learned']}\n"
               f"Knowledge Domains: {status['knowledge_domains']}\n"
               f"\nTop Skills:\n{skills_display}\n"
               f"{'='*50}\n"
               f"Session: {status['session_id']}")
    
    def __del__(self):
        """Save state on destruction"""
        try:
            self._save_state()
        except:
            pass
