#!/usr/bin/env python3
"""
Saraphina Terminal Enhanced - Interactive AI with Persistent Learning
Features: State persistence, conversation export, rich status displays, domain knowledge
"""

import sys
from pathlib import Path
from datetime import datetime

# Add saraphina to path
sys.path.insert(0, str(Path(__file__).parent))

from saraphina.ai_core_enhanced import SaraphinaAIEnhanced


def print_banner():
    """Print enhanced welcome banner"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║     🌟 SARAPHINA ENHANCED AI TERMINAL 🌟                    ║
║     Advanced Learning AI with Persistent Intelligence        ║
╚══════════════════════════════════════════════════════════════╝

Welcome! I'm Saraphina 3.0 Enhanced - your learning AI assistant.

🎯 NEW FEATURES:
  • Persistent learning across sessions
  • 7 knowledge domains (Programming, Cloud, DevOps, Web, Security, etc.)
  • Conversation history export
  • Advanced progress tracking
  • Auto-save every 5 conversations

📚 KNOWLEDGE DOMAINS:
  Programming Languages  | System Administration | Cloud Platforms
  DevOps & CI/CD        | Web Development       | Security
  Data Science & ML     | And more!

Commands:
  /status   - Show learning status with progress bars
  /export   - Export conversation history
  /help     - Show all commands
  /domains  - List knowledge domains
  /exit     - Exit (auto-saves)

Just type naturally to chat with me!
""")


def print_help():
    """Print comprehensive help"""
    print("""
🌟 SARAPHINA ENHANCED TERMINAL - COMMANDS

CONVERSATION:
  Just type naturally - I understand context and learn from you!
  
SYSTEM COMMANDS:
  /status   - Show detailed AI learning status with progress bars
  /export   - Export conversation history to JSON file
  /domains  - List all knowledge domains I have expertise in
  /help     - Show this help message  
  /exit     - Exit terminal (auto-saves learning state)
  /quit     - Same as /exit

ADVANCED QUERIES:
  Ask me about:
    • Programming (Python, JavaScript, etc.)
    • Cloud platforms (AWS, Azure, GCP)
    • DevOps (Docker, Kubernetes, CI/CD)
    • Web development (React, APIs, databases)
    • Security (encryption, authentication)
    • Data science (ML, deep learning)
    • System administration (Windows, Linux)

EXAMPLES:
  > Hello Saraphina
  > Who are you?
  > What's your expertise in Python?
  > Tell me about Docker and Kubernetes
  > How do I secure my API?
  > What's your learning status?
  > /domains

💡 PERSISTENT LEARNING:
  • Your progress is automatically saved
  • I remember conversations across sessions
  • Skills improve with each interaction
  • Intelligence levels carry over

🎯 XP SYSTEM:
  • Simple queries: +1 XP
  • Technical questions: +4 XP
  • Learning discussions: +6 XP
  • Level up every 100 XP
""")


def print_domains(ai):
    """Print all knowledge domains"""
    print("\n" + "="*60)
    print("🎓 SARAPHINA KNOWLEDGE DOMAINS")
    print("="*60)
    
    domains = {
        'Programming Languages': [
            'Python (Django, Flask, FastAPI, ML)',
            'JavaScript (React, Node.js, TypeScript)',
            'Java, C#, Go, Rust, PHP, Ruby, Swift'
        ],
        'System Administration': [
            'Windows (PowerShell, Active Directory)',
            'Linux (Bash, systemd, Networking)',
            'macOS (Terminal, Homebrew)'
        ],
        'Cloud Platforms': [
            'AWS (EC2, S3, Lambda, RDS, IAM)',
            'Azure (VMs, Functions, SQL Database)',
            'GCP (Compute, Storage, BigQuery)'
        ],
        'DevOps': [
            'Docker, Kubernetes, Helm',
            'CI/CD (Jenkins, GitHub Actions)',
            'IaC (Terraform, Ansible)'
        ],
        'Web Development': [
            'Frontend (React, Vue, Angular)',
            'Backend (REST, GraphQL, Microservices)',
            'Databases (PostgreSQL, MongoDB, Redis)'
        ],
        'Security': [
            'Authentication (OAuth, JWT)',
            'Encryption (SSL/TLS, HTTPS)',
            'Security Testing & Penetration'
        ],
        'Data Science': [
            'Machine Learning (scikit-learn, TensorFlow)',
            'Deep Learning (PyTorch, NLP, Computer Vision)',
            'Data Analysis (Pandas, NumPy, Matplotlib)'
        ]
    }
    
    for domain, topics in domains.items():
        print(f"\n📂 {domain}")
        for topic in topics:
            print(f"   • {topic}")
    
    print("\n" + "="*60)
    print(f"🎯 Total Expertise: {len(domains)} major domains")
    print(f"💡 Intelligence Level: {ai.intelligence_level}")
    print(f"📚 Total XP: {ai.experience_points}")
    print("="*60 + "\n")


def main():
    """Main enhanced terminal loop"""
    print_banner()
    
    # Initialize Enhanced AI
    try:
        ai = SaraphinaAIEnhanced()
        
        # Show loaded state if continuing
        if ai.total_conversations > 0:
            print(f"\n📊 Continuing from previous session:")
            print(f"   Level {ai.intelligence_level} | {ai.experience_points} XP | "
                  f"{ai.total_conversations} total conversations")
        
        print(f"\n✅ AI Core Enhanced loaded")
        print(f"   Session: {ai.session_id}")
        print(f"   Data Dir: {ai.data_dir.absolute()}\n")
    except Exception as e:
        print(f"❌ Error initializing AI: {e}")
        return 1
    
    # Main loop
    while True:
        try:
            user_input = input("\n💬 You: ").strip()
            
            if not user_input:
                continue
            
            # Exit commands
            if user_input.lower() in ['/exit', '/quit', 'exit', 'quit']:
                print("\n👋 Goodbye! Saving your progress...")
                ai._save_state()
                print("\n" + "="*60)
                print(ai.get_status_summary())
                print("="*60)
                print("\n✅ All progress saved. See you next time!")
                break
            
            # Help command
            if user_input.lower() in ['/help', 'help']:
                print_help()
                continue
            
            # Status command
            if user_input.lower() in ['/status', 'status']:
                print("\n" + ai.get_status_summary())
                continue
            
            # Export command
            if user_input.lower() in ['/export']:
                filename = ai.export_conversation_history()
                print(f"\n✅ Conversation exported to: {filename}")
                print(f"📊 Exported {len(ai.conversation_history)} messages")
                continue
            
            # Domains command
            if user_input.lower() in ['/domains']:
                print_domains(ai)
                continue
            
            # Process with AI
            response = ai.process_query(user_input)
            print(f"\n🤖 Saraphina: {response}")
            
            # Show XP gain feedback
            if ai.total_conversations % 10 == 0:
                print(f"\n💫 Milestone! {ai.total_conversations} conversations completed")
                print(f"   Current: Level {ai.intelligence_level} | {ai.experience_points} XP")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye! Saving your progress...")
            ai._save_state()
            print(f"\n✅ Progress saved. Level {ai.intelligence_level} with {ai.experience_points} XP")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Don't worry, I'm learning from this experience!")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
