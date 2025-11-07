#!/usr/bin/env python3
"""
Saraphina Terminal - Interactive AI Assistant
Enhanced with learning capabilities from vjr_terminal.py
"""

import sys
from pathlib import Path

# Add saraphina to path
sys.path.insert(0, str(Path(__file__).parent))

from saraphina.ai_core import SaraphinaAI


def print_banner():
    """Print welcome banner"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║        🌟 SARAPHINA INTERACTIVE TERMINAL 🌟                 ║
║        Advanced AI Assistant with Learning                   ║
╚══════════════════════════════════════════════════════════════╝

Welcome! I'm Saraphina, your learning AI assistant.
I grow smarter with each conversation - currently tracking:
  • Intelligence Level & Experience Points
  • Memory Bank of interactions
  • Pattern recognition and learning

Commands:
  /status  - Show my learning status
  /help    - Show available commands
  /exit    - Exit (or Ctrl+C)

Just type naturally to chat with me!
""")


def print_help():
    """Print help information"""
    print("""
🌟 SARAPHINA TERMINAL - COMMANDS

CONVERSATION:
  Just type naturally - I'll respond intelligently!
  
SYSTEM COMMANDS:
  /status   - Show AI learning status and stats
  /help     - Show this help message  
  /exit     - Exit the terminal
  /quit     - Exit the terminal

EXAMPLES:
  > Hello Saraphina
  > Who are you?
  > What can you do?
  > Tell me about your learning
  > How intelligent are you?

💡 TIP: I learn from every interaction and level up as I gain experience!
""")


def main():
    """Main terminal loop"""
    print_banner()
    
    # Initialize AI
    try:
        ai = SaraphinaAI()
        print(f"✅ AI Core loaded - {ai.get_status_summary()}\n")
    except Exception as e:
        print(f"❌ Error initializing AI: {e}")
        return 1
    
    # Main loop
    while True:
        try:
            user_input = input("\n💬 You: ").strip()
            
            if not user_input:
                continue
            
            # Check for exit commands
            if user_input.lower() in ['/exit', '/quit', 'exit', 'quit']:
                print("\n👋 Goodbye! Thanks for chatting with me.")
                print("\n" + "="*60)
                print(ai.get_status_summary())
                print("="*60)
                break
            
            # Check for help command
            if user_input.lower() in ['/help', 'help']:
                print_help()
                continue
            
            # Check for status command
            if user_input.lower() in ['/status', 'status']:
                print("\n" + "="*60)
                print(ai.get_status_summary())
                print("="*60)
                print("\n💡 Keep chatting to help me grow smarter!")
                continue
            
            # Process natural language with AI
            response = ai.process_query(user_input)
            print(f"\n🤖 Saraphina: {response}")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye! Thanks for using Saraphina Terminal.")
            print("\n" + ai.get_status_summary())
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Don't worry, I'm learning from this experience!")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
