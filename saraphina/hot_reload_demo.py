#!/usr/bin/env python3
"""
Hot-Reload Demo Module

A simple module for demonstrating hot-reload capabilities.
This can be modified and reloaded without restarting Saraphina.
"""

def greet(name: str) -> str:
    """
    Simple greeting function.
    
    Args:
        name: Name to greet
        
    Returns:
        Greeting message
    """
    return f"Hello, {name}!"


def calculate(x: int, y: int) -> int:
    """
    Simple calculation function.
    
    Args:
        x: First number
        y: Second number
        
    Returns:
        Sum of x and y
    """
    return x + y


class DemoClass:
    """Demonstration class for hot-reload."""
    
    def __init__(self, value: str):
        """Initialize with a value."""
        self.value = value
    
    def get_value(self) -> str:
        """Return the stored value."""
        return self.value
    
    def process(self) -> str:
        """Process the value."""
        return self.value.upper()


# Module-level constant
VERSION = "1.0.0"
