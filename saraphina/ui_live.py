#!/usr/bin/env python3
"""
Live UI wrapper for Saraphina - manages real-time UI updates
"""

import threading
import time
from typing import Optional
from contextlib import contextmanager

try:
    from rich.live import Live
    from rich.console import Console
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from saraphina.ui_manager import SaraphinaUI


class LiveUIContext:
    """Context manager for live UI updates"""
    
    def __init__(self, ui: SaraphinaUI):
        self.ui = ui
        self.live: Optional[Live] = None
        self.update_thread: Optional[threading.Thread] = None
        self.running = False
        self.refresh_rate = 1.0  # 1 FPS - much slower to prevent glitching
        self.last_update = 0
        self.update_buffer_time = 0.5  # Don't update more than twice per second
        
    def __enter__(self):
        """Start live UI display"""
        if not self.ui.enabled:
            return self
        
        self.running = True
        self.live = Live(
            self.ui.render(),
            console=self.ui.console,
            refresh_per_second=5,
            transient=False
        )
        self.live.__enter__()
        
        # DON'T start background thread - causes glitching
        # Only update on explicit calls to prevent flicker
        # self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        # self.update_thread.start()
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop live UI display"""
        self.running = False
        
        if self.update_thread:
            self.update_thread.join(timeout=1.0)
        
        if self.live:
            self.live.__exit__(exc_type, exc_val, exc_tb)
    
    def _update_loop(self):
        """Background loop to update UI for animations"""
        while self.running:
            try:
                if self.live:
                    # Only update if enough time has passed (prevent rapid flicker)
                    current_time = time.time()
                    if current_time - self.last_update >= self.update_buffer_time:
                        self.live.update(self.ui.render())
                        self.last_update = current_time
                time.sleep(self.refresh_rate)
            except Exception:
                pass
    
    def update(self):
        """Force immediate UI update with throttling"""
        if self.live and self.ui.enabled:
            try:
                # Throttle updates to prevent glitching
                current_time = time.time()
                if current_time - self.last_update >= self.update_buffer_time:
                    self.live.update(self.ui.render())
                    self.last_update = current_time
            except Exception:
                pass


@contextmanager
def live_ui(ui: SaraphinaUI):
    """Context manager for live UI display"""
    ctx = LiveUIContext(ui)
    try:
        yield ctx.__enter__()
    finally:
        ctx.__exit__(None, None, None)


def create_live_context(ui: SaraphinaUI) -> LiveUIContext:
    """Create a live UI context"""
    return LiveUIContext(ui)
