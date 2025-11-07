#!/usr/bin/env python3
"""
Demo script to preview Saraphina's futuristic UI
Run this to see the mission control interface in action
"""

import time
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from saraphina.ui_manager import SaraphinaUI
from saraphina.ui_live import LiveUIContext

def demo():
    """Run UI demo with sample data"""
    
    # Create UI
    ui = SaraphinaUI()
    
    if not ui.enabled:
        print("❌ Rich library not available. Install with: pip install rich")
        ui.print_banner_fallback()
        return
    
    # Set initial status
    ui.update_status(
        level=3,
        xp=247,
        session_id='ai_20251105_demo',
        voice_enabled=True,
        security_ok=True,
        modules_loaded=['Knowledge', 'Planner', 'Voice', 'Security', 'Ethics']
    )
    
    # Add some conversation history
    ui.add_message('Jacques', 'Hello Saraphina!')
    ui.add_message('Saraphina', 'Hello Jacques! I\'m ready to assist you. 🌌')
    
    ui.add_diagnostic('AI Core initialized')
    ui.add_diagnostic('Voice system ready')
    ui.add_diagnostic('Knowledge Engine connected')
    
    # Start live UI
    ctx = LiveUIContext(ui)
    
    try:
        print("╔════════════════════════════════════════════════════════════════╗")
        print("║         SARAPHINA ULTRA UI DEMO - PRESS CTRL+C TO EXIT        ║")
        print("╚════════════════════════════════════════════════════════════════╝\n")
        
        with ctx:
            # Simulate conversation with delays
            time.sleep(2)
            
            ui.add_message('Jacques', 'What can you do?')
            ctx.update()
            time.sleep(2)
            
            ui.add_message('Saraphina', 'I can help with planning, knowledge retrieval, code analysis, ethical reasoning, and much more!')
            ctx.update()
            time.sleep(2)
            
            ui.add_message('Jacques', 'Show me your status')
            ctx.update()
            time.sleep(1)
            
            ui.add_diagnostic('Status query received')
            ctx.update()
            time.sleep(1)
            
            ui.add_message('Saraphina', 'All systems operational. Level 3 with 247 XP. Voice and security active.')
            ctx.update()
            time.sleep(2)
            
            # Simulate voice speaking
            ui.add_message('Jacques', 'Say something')
            ctx.update()
            time.sleep(1)
            
            ui.set_speaking(True)
            ui.add_message('Saraphina', 'I\'m speaking now! Watch the waveform in the status panel. ⚡')
            ctx.update()
            time.sleep(3)
            
            ui.set_speaking(False)
            ctx.update()
            time.sleep(1)
            
            ui.add_message('Jacques', 'That looks great!')
            ctx.update()
            time.sleep(2)
            
            ui.add_message('Saraphina', 'Thank you! This is my new futuristic mission control interface. 🚀')
            ui.add_diagnostic('Demo complete')
            ctx.update()
            
            # Keep running
            print("\n\nDemo running... Press CTRL+C to exit\n")
            while True:
                time.sleep(1)
                
    except KeyboardInterrupt:
        print("\n\n✅ Demo terminated. UI looks great!")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")


if __name__ == '__main__':
    demo()
