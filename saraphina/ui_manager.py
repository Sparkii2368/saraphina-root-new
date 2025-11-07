#!/usr/bin/env python3
"""
Saraphina UI Manager - Futuristic Mission Control Interface
Creates a living AI cockpit with neon aesthetics and HUD-style displays
"""

import time
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

try:
    from rich.console import Console
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.live import Live
    from rich.table import Table
    from rich.progress import Progress, BarColumn, TextColumn, SpinnerColumn
    from rich.text import Text
    from rich.align import Align
    from rich.columns import Columns
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class SaraphinaUI:
    """Futuristic terminal UI manager with mission control aesthetics"""
    
    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        self.enabled = RICH_AVAILABLE
        
        # UI State
        self.conversation_log: List[Dict[str, str]] = []
        self.diagnostics_log: List[str] = []
        self.max_conversation = 20  # Keep last 20 messages
        self.max_diagnostics = 10   # Keep last 10 diagnostic entries
        self.show_diagnostics = False
        
        # Status data
        self.status_data = {
            'level': 1,
            'xp': 0,
            'session_id': 'unknown',
            'voice_enabled': False,
            'security_ok': True,
            'modules_loaded': [],
            'uptime_start': datetime.now()
        }
        
        # Animation state
        self.pulse_frame = 0
        self.is_speaking = False
        
        # Neon color theme
        self.colors = {
            'primary': 'bright_cyan',
            'secondary': 'bright_magenta',
            'accent': 'bright_blue',
            'success': 'bright_green',
            'warning': 'bright_yellow',
            'error': 'bright_red',
            'muted': 'bright_black'
        }
    
    def pulse_animation(self) -> str:
        """Static indicator - animations removed to prevent glitching"""
        return '●'  # Static dot instead of animated
    
    def voice_waveform(self) -> str:
        """Simple voice indicator - animations removed to prevent glitching"""
        if not self.is_speaking:
            return '▁▁▁▁▁'
        return '█████'  # Static bars when speaking
    
    def format_uptime(self) -> str:
        """Format session uptime"""
        delta = datetime.now() - self.status_data['uptime_start']
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def create_header(self) -> Panel:
        """Create futuristic header banner with pulsing life indicator"""
        pulse = self.pulse_animation()
        uptime = self.format_uptime()
        
        title_text = Text()
        title_text.append("SARAPHINA", style=f"bold {self.colors['primary']}")
        # Removed 'ULTRA' branding
        title_text.append(" AI TERMINAL", style=f"bold {self.colors['secondary']}")
        
        subtitle = Text()
        subtitle.append(f"{pulse} SYSTEM ACTIVE ", style=f"{self.colors['success']}")
        subtitle.append(f"│ SESSION: {uptime}", style=self.colors['muted'])
        
        content = Align.center(Text.assemble(title_text, "\n", subtitle))
        
        return Panel(
            content,
            border_style=self.colors['primary'],
            box=box.DOUBLE_EDGE,
            padding=(0, 2)
        )
    
    def create_status_panel(self) -> Panel:
        """Create compact status sidebar with icons and color codes"""
        table = Table.grid(padding=(0, 1))
        table.add_column(style=self.colors['accent'], justify="left")
        table.add_column(style="white", justify="left")
        
        # Intelligence Level with XP bar
        level = self.status_data.get('level', 1)
        xp = self.status_data.get('xp', 0)
        xp_percent = min(100, int((xp % 100) / 100 * 100))
        xp_bar = '█' * (xp_percent // 10) + '░' * (10 - xp_percent // 10)
        
        table.add_row("🧠 Intelligence", f"Level {level}")
        table.add_row("", f"[{self.colors['primary']}]{xp_bar}[/] {xp} XP")
        table.add_row("", "")
        
        # Security Status
        security_icon = "✓" if self.status_data.get('security_ok') else "⚠️"
        security_color = self.colors['success'] if self.status_data.get('security_ok') else self.colors['warning']
        table.add_row("🔐 Security", f"[{security_color}]{security_icon}[/]")
        
        # Voice Status
        voice_icon = "●" if self.status_data.get('voice_enabled') else "○"
        voice_color = self.colors['success'] if self.status_data.get('voice_enabled') else self.colors['muted']
        voice_wave = self.voice_waveform() if self.status_data.get('voice_enabled') else ''
        table.add_row("🎤 Voice", f"[{voice_color}]{voice_icon}[/] {voice_wave}")
        
        table.add_row("", "")
        
        # Modules
        modules = self.status_data.get('modules_loaded', [])
        table.add_row("📦 Modules", f"{len(modules)} active")
        for mod in modules[:3]:  # Show first 3
            table.add_row("", f"[{self.colors['muted']}]• {mod}[/]")
        
        table.add_row("", "")
        
        # Session ID
        session = self.status_data.get('session_id', 'unknown')[:12]
        table.add_row("🆔 Session", f"[{self.colors['muted']}]{session}[/]")
        
        return Panel(
            table,
            title="[bold]SYSTEM STATUS[/bold]",
            border_style=self.colors['secondary'],
            box=box.ROUNDED,
            padding=(1, 2)
        )
    
    def create_conversation_panel(self) -> Panel:
        """Create main conversation area with speech-bubble style"""
        if not self.conversation_log:
            placeholder = Text("Ready for interaction...", style=self.colors['muted'], justify="center")
            return Panel(
                Align.center(placeholder, vertical="middle"),
                title="[bold]MAIN CONSOLE[/bold]",
                border_style=self.colors['primary'],
                box=box.HEAVY,
                padding=(1, 2),
                height=20
            )
        
        # Build conversation view
        conv_text = Text()
        
        for msg in self.conversation_log[-10:]:  # Last 10 messages
            speaker = msg.get('speaker', 'unknown')
            content = msg.get('content', '')
            
            if speaker.lower() == 'user':
                # User message - cyan
                conv_text.append(f"▶ {speaker}: ", style=f"bold {self.colors['primary']}")
                conv_text.append(f"{content}\n\n", style="white")
            else:
                # Saraphina message - magenta
                conv_text.append(f"◀ {speaker}: ", style=f"bold {self.colors['secondary']}")
                conv_text.append(f"{content}\n\n", style="white")
        
        return Panel(
            conv_text,
            title="[bold]MAIN CONSOLE[/bold]",
            border_style=self.colors['primary'],
            box=box.HEAVY,
            padding=(1, 2),
            height=20
        )
    
    def create_diagnostics_panel(self) -> Optional[Panel]:
        """Create collapsible diagnostics ticker (bottom panel)"""
        if not self.show_diagnostics:
            return None
        
        diag_text = Text()
        
        for entry in self.diagnostics_log[-self.max_diagnostics:]:
            timestamp = datetime.now().strftime('%H:%M:%S')
            diag_text.append(f"[{timestamp}] ", style=self.colors['muted'])
            diag_text.append(f"{entry}\n", style=self.colors['accent'])
        
        return Panel(
            diag_text,
            title="[bold]DIAGNOSTICS FEED[/bold]",
            border_style=self.colors['accent'],
            box=box.SIMPLE,
            padding=(0, 1),
            height=8
        )
    
    def create_quick_commands(self) -> Panel:
        """Create quick command palette"""
        commands = [
            ("help", "Show all commands"),
            ("recall", "Search knowledge"),
            ("plan", "Create action plan"),
            ("ethics", "Ethics check"),
            ("status", "System status")
        ]
        
        cmd_columns = []
        for cmd, desc in commands:
            cmd_text = Text()
            cmd_text.append(f"/{cmd}", style=f"bold {self.colors['primary']}")
            cmd_text.append(f"\n{desc}", style=self.colors['muted'])
            cmd_columns.append(Panel(cmd_text, border_style=self.colors['accent'], box=box.SIMPLE, padding=(0, 1)))
        
        return Panel(
            Columns(cmd_columns, equal=True, expand=True),
            title="[bold]QUICK COMMANDS[/bold]",
            border_style=self.colors['accent'],
            box=box.SIMPLE,
            padding=(0, 1)
        )
    
    def create_layout(self) -> Layout:
        """Create main mission control layout"""
        layout = Layout()
        
        # Split into header, body, footer
        layout.split_column(
            Layout(name="header", size=5),
            Layout(name="body"),
            Layout(name="footer", size=4)
        )
        
        # Split body into main console and sidebar
        layout["body"].split_row(
            Layout(name="console", ratio=3),
            Layout(name="sidebar", ratio=1, minimum_size=30)
        )
        
        # Populate components
        layout["header"].update(self.create_header())
        layout["console"].update(self.create_conversation_panel())
        layout["sidebar"].update(self.create_status_panel())
        layout["footer"].update(self.create_quick_commands())
        
        return layout
    
    def update_status(self, **kwargs):
        """Update status data"""
        self.status_data.update(kwargs)
    
    def add_message(self, speaker: str, content: str):
        """Add a message to conversation log"""
        self.conversation_log.append({
            'speaker': speaker,
            'content': content,
            'timestamp': datetime.now()
        })
        
        # Trim to max
        if len(self.conversation_log) > self.max_conversation:
            self.conversation_log = self.conversation_log[-self.max_conversation:]
    
    def add_diagnostic(self, message: str):
        """Add a diagnostic log entry"""
        self.diagnostics_log.append(message)
        
        # Trim to max
        if len(self.diagnostics_log) > self.max_diagnostics:
            self.diagnostics_log = self.diagnostics_log[-self.max_diagnostics:]
    
    def set_speaking(self, is_speaking: bool):
        """Set voice speaking state for waveform animation"""
        self.is_speaking = is_speaking
    
    def toggle_diagnostics(self):
        """Toggle diagnostics panel visibility"""
        self.show_diagnostics = not self.show_diagnostics
    
    def render(self) -> Layout:
        """Render the complete UI layout"""
        return self.create_layout()
    
    def print_banner_fallback(self):
        """Fallback ASCII banner if Rich not available"""
        print("""
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║                    SARAPHINA AI TERMINAL                                 ║
║             Futuristic Mission Control Interface                         ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
""")
    
    def clear_screen(self):
        """Clear terminal screen"""
        import os
        os.system('cls' if os.name == 'nt' else 'clear')


# Utility functions for integration
def create_ui() -> SaraphinaUI:
    """Create and return UI manager instance"""
    return SaraphinaUI()


def format_greeting(ui: SaraphinaUI, owner_name: str, level: int) -> str:
    """Format greeting message with proper styling"""
    return f"Hello {owner_name}! I'm Saraphina—voice-enabled and adaptive. I'm currently level {level}. How can I help today?"
