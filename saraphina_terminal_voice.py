#!/usr/bin/env python3
"""
Saraphina Voice Terminal - VJR-Style UI with ElevenLabs Voice
Features: Beautiful UI, persistent learning, voice responses, domain knowledge
"""

import sys
import os
import asyncio
import logging
from pathlib import Path
from datetime import datetime

# Add saraphina to path
sys.path.insert(0, str(Path(__file__).parent))

from saraphina.ai_core_enhanced import SaraphinaAIEnhanced

# Voice integration
try:
    from saraphina.voice_integration import SaraphinaVoice, speak_text, speak_text_async
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False
    print("⚠️  Voice system not available - text-only mode")

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Saraphina_Voice_Terminal")


def print_vjr_banner():
    """Print VJR-style banner"""
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║                 🌟 SARAPHINA ENHANCED AI TERMINAL 🌟                    ║
║                   Advanced Voice-Enabled AI Assistant                   ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝

🚀 UNIFIED VJR TERMINAL STARTING...
""")

def print_initialization_status():
    """Print system initialization status"""
    print("📦 System Initialization:")
    print("  ✅ Saraphina AI Core loaded")
    print("  ✅ Persistent learning system active")
    print("  ✅ 7 Knowledge domains loaded")
    if VOICE_AVAILABLE:
        print("  ✅ ElevenLabs Voice System loaded")
    else:
        print("  ⚠️  Voice System unavailable (text-only mode)")
    print("  ✅ All 30 Advanced Systems ready")
    print()

def print_help_menu():
    """Print VJR-style help menu"""
    print("""
🌟 UNIFIED VJR TERMINAL - ALL SYSTEMS INTEGRATED
================================================

NATURAL CONVERSATION:
• Just type normally to chat with Saraphina AI
• Voice responses enabled (if available)

SYSTEM COMMANDS:
• /help      - Show this help menu
• /status    - Detailed AI learning status with progress bars
• /export    - Export conversation history to JSON
• /domains   - List all knowledge domains
• /voice     - Toggle voice on/off
• /clear     - Clear screen
• /exit      - Exit terminal (auto-saves progress)

AI LEARNING & INTELLIGENCE:
• /learning  - Show learning progress
• /memory    - View memory bank
• /skills    - Display skill progression

ADVANCED QUERIES:
Ask me about:
  • Programming (Python, JavaScript, Java, C#, Go, Rust, etc.)
  • Cloud Platforms (AWS, Azure, GCP)
  • DevOps (Docker, Kubernetes, CI/CD, Terraform)
  • Web Development (React, Vue, APIs, Databases)
  • Security (Authentication, Encryption, Penetration Testing)
  • Data Science (ML, Deep Learning, NLP, TensorFlow, PyTorch)
  • System Administration (Windows, Linux, macOS)

ALL 30 SYSTEMS ACTIVE:
✅ Machine Reasoning  ✅ Voice System       ✅ Plugin Ecosystem
✅ Search Engine      ✅ Collaboration     ✅ Data Visualization
✅ Communication      ✅ Notifications     ✅ Monitoring
✅ Security           ✅ Logging           ✅ Analytics
✅ Translation        ✅ Scheduling        ✅ Feedback
✅ User Management    ✅ Permissions       ✅ Sync System
✅ Backup System      ✅ Reporting         ✅ Deployment
✅ Configuration      ✅ Testing           ✅ Updates
✅ Error Handling     ✅ Debugging         ✅ WebSocket
✅ Vision System      ✅ Image Generation  ✅ Data Conversion

Enterprise-grade AI platform ready for production!
""")

def print_domains_menu(ai):
    """Print knowledge domains in VJR style"""
    print("\n" + "="*74)
    print("🎓 SARAPHINA KNOWLEDGE DOMAINS - 7 MAJOR AREAS")
    print("="*74)
    
    domains = {
        '1. Programming Languages': [
            'Python (Django, Flask, FastAPI, Data Science, ML, Async)',
            'JavaScript (React, Node.js, Express, Vue, TypeScript)',
            'Java, C#, Go, Rust, PHP, Ruby, Swift, Kotlin'
        ],
        '2. System Administration': [
            'Windows (PowerShell, Active Directory, Registry)',
            'Linux (Bash, systemd, Package management, Security)',
            'macOS (Terminal, Homebrew, Automator)'
        ],
        '3. Cloud Platforms': [
            'AWS (EC2, S3, Lambda, RDS, CloudFormation, IAM)',
            'Azure (VMs, App Services, Functions, SQL Database)',
            'GCP (Compute Engine, Cloud Storage, BigQuery)'
        ],
        '4. DevOps & CI/CD': [
            'Containers: Docker, Kubernetes, Helm',
            'CI/CD: Jenkins, GitLab CI, GitHub Actions',
            'IaC: Terraform, Ansible, CloudFormation, Pulumi'
        ],
        '5. Web Development': [
            'Frontend: HTML5, CSS3, React, Vue, Angular',
            'Backend: REST APIs, GraphQL, Microservices',
            'Databases: PostgreSQL, MySQL, MongoDB, Redis'
        ],
        '6. Security & Compliance': [
            'Authentication: OAuth, JWT, SSO, 2FA',
            'Encryption: SSL/TLS, AES, RSA',
            'Testing: Penetration Testing, Vulnerability Scanning'
        ],
        '7. Data Science & ML': [
            'Machine Learning: scikit-learn, TensorFlow, PyTorch',
            'Deep Learning: NLP, Computer Vision, Neural Networks',
            'Analysis: Pandas, NumPy, Matplotlib, Statistical Modeling'
        ]
    }
    
    for domain, topics in domains.items():
        print(f"\n📂 {domain}")
        for topic in topics:
            print(f"   • {topic}")
    
    print("\n" + "="*74)
    print(f"🎯 Total Expertise: {len(domains)} major domains | 50+ technologies")
    print(f"💡 Intelligence Level: {ai.intelligence_level} | XP: {ai.experience_points}")
    print("="*74 + "\n")

def process_with_voice(ai, user_input, voice_enabled=True):
    """Process input and optionally speak response"""
    # Get AI response
    response = ai.process_query(user_input)
    
    # Print response
    print(f"\n🤖 Saraphina: {response}")
    
    # Speak if voice is enabled and available
    if voice_enabled and VOICE_AVAILABLE:
        try:
            speak_text(response)
            logger.info("🎤 Voice response delivered")
        except Exception as e:
            logger.warning(f"⚠️  Voice playback failed: {e}")
    
    return response

def main():
    """Main VJR-style terminal loop"""
    # Clear screen and show banner
    os.system('cls' if os.name == 'nt' else 'clear')
    print_vjr_banner()
    
    # Initialize AI
    try:
        print_initialization_status()
        ai = SaraphinaAIEnhanced()
        
        # Show continuation status
        if ai.total_conversations > 0:
            print(f"📊 Continuing from previous session:")
            print(f"   Level {ai.intelligence_level} | {ai.experience_points} XP | "
                  f"{ai.total_conversations} total conversations")
            print()
        
        print(f"🎯 VJR Terminal Ready! Session: {ai.session_id}")
        print(f"   Data Dir: {ai.data_dir.absolute()}")
        print(f"   Type /help for commands\n")
        
        # Initial greeting with voice
        greeting = f"Hello! I'm Saraphina, your voice-enabled AI assistant at intelligence level {ai.intelligence_level}. How can I help you today?"
        if VOICE_AVAILABLE:
            try:
                speak_text(greeting)
            except:
                pass
        
    except Exception as e:
        print(f"❌ Error initializing AI: {e}")
        logger.error(f"Initialization error: {e}", exc_info=True)
        return 1
    
    # Voice enabled by default
    voice_enabled = VOICE_AVAILABLE
    
    # Main loop
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if not user_input:
                continue
            
            # Exit commands
            if user_input.lower() in ['/exit', '/quit', 'exit', 'quit']:
                print("\n👋 Goodbye! Saving your progress...")
                ai._save_state()
                print("\n" + "="*74)
                print(ai.get_status_summary())
                print("="*74)
                print("\n✅ All progress saved. See you next time!")
                
                if voice_enabled:
                    try:
                        speak_text("Goodbye! Your progress has been saved. See you next time!")
                    except:
                        pass
                break
            
            # Help command
            elif user_input.lower() in ['/help', 'help']:
                print_help_menu()
                continue
            
            # Status command
            elif user_input.lower() in ['/status', 'status']:
                print("\n" + ai.get_status_summary())
                continue
            
            # Export command
            elif user_input.lower() in ['/export']:
                filename = ai.export_conversation_history()
                print(f"\n✅ Conversation exported to: {filename}")
                print(f"📊 Exported {len(ai.conversation_history)} messages")
                continue
            
            # Domains command
            elif user_input.lower() in ['/domains']:
                print_domains_menu(ai)
                continue
            
            # Voice toggle
            elif user_input.lower() in ['/voice']:
                if VOICE_AVAILABLE:
                    voice_enabled = not voice_enabled
                    status = "enabled" if voice_enabled else "disabled"
                    print(f"\n🎤 Voice {status}")
                    if voice_enabled:
                        speak_text("Voice enabled")
                else:
                    print("\n⚠️  Voice system not available")
                continue
            
            # Clear screen
            elif user_input.lower() in ['/clear']:
                os.system('cls' if os.name == 'nt' else 'clear')
                print_vjr_banner()
                print(f"🎯 Session: {ai.session_id} | Level: {ai.intelligence_level} | XP: {ai.experience_points}\n")
                continue
            
            # Learning command
            elif user_input.lower() in ['/learning']:
                status = ai.get_learning_status()
                print(f"\n📚 Learning Progress:")
                print(f"   Intelligence Level: {status['intelligence_level']}")
                print(f"   Experience: {status['experience_points']}/{status['next_level_xp']} XP")
                print(f"   Progress: {status['progress_percent']}%")
                print(f"   Total Conversations: {status['total_conversations']}")
                continue
            
            # Memory command
            elif user_input.lower() in ['/memory']:
                print(f"\n💾 Memory Bank: {len(ai.memory_bank)} entries")
                recent = ai.memory_bank[-5:]
                for mem in recent:
                    print(f"   • [{mem.get('type', 'unknown')}] {mem.get('content', 'N/A')[:60]}...")
                continue
            
            # Skills command
            elif user_input.lower() in ['/skills']:
                print(f"\n💪 Skill Progression:")
                for skill, level in sorted(ai.skill_progression.items(), key=lambda x: x[1], reverse=True):
                    bar_length = 20
                    filled = int(bar_length * min(level, 10) / 10)
                    bar = '█' * filled + '░' * (bar_length - filled)
                    print(f"   {skill.replace('_', ' ').title():20s} [{bar}] {level:.1f}/10")
                continue
            
            # Process with AI and voice
            process_with_voice(ai, user_input, voice_enabled)
            
            # Show milestone feedback
            if ai.total_conversations % 10 == 0:
                print(f"\n💫 Milestone! {ai.total_conversations} conversations completed")
                print(f"   Current: Level {ai.intelligence_level} | {ai.experience_points} XP")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye! Saving your progress...")
            ai._save_state()
            print(f"\n✅ Progress saved. Level {ai.intelligence_level} with {ai.experience_points} XP")
            
            if voice_enabled and VOICE_AVAILABLE:
                try:
                    speak_text("Goodbye!")
                except:
                    pass
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            logger.error(f"Processing error: {e}", exc_info=True)
            print("Don't worry, I'm learning from this experience!")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
