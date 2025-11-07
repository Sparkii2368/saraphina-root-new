#!/usr/bin/env python3
"""
Error Sentinel - Autonomic Error Detection & Self-Healing
Wraps every subsystem with error detection, logging, and auto-healing
"""

import sys
import traceback
import logging
import hashlib
from datetime import datetime
from typing import Callable, Any, Optional, Dict
from functools import wraps
from pathlib import Path

logger = logging.getLogger("ErrorSentinel")


class ErrorBus:
    """Central error event bus"""
    
    def __init__(self):
        self.listeners = []
        self.error_count = 0
    
    def subscribe(self, listener: Callable):
        """Subscribe to error events"""
        self.listeners.append(listener)
    
    def publish(self, error_event: Dict):
        """Publish error event to all listeners"""
        self.error_count += 1
        for listener in self.listeners:
            try:
                listener(error_event)
            except Exception as e:
                logger.error(f"Error in listener: {e}")


# Global error bus
_error_bus = ErrorBus()


def get_error_bus() -> ErrorBus:
    """Get global error bus"""
    return _error_bus


class ErrorSentinel:
    """Wraps subsystems with error detection and auto-healing"""
    
    def __init__(self, subsystem_name: str, auto_heal: bool = True, require_approval: bool = False):
        self.subsystem_name = subsystem_name
        self.auto_heal = auto_heal
        self.require_approval = require_approval
        self.error_kb = None  # Will be set by ErrorKnowledgeBase
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator to wrap function with sentinel"""
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Normal execution
                return func(*args, **kwargs)
                
            except Exception as e:
                # Error occurred - capture context
                error_event = self._capture_error(e, func, args, kwargs)
                
                # Publish to error bus
                get_error_bus().publish(error_event)
                
                # Try to auto-heal if enabled
                if self.auto_heal and not self.require_approval:
                    healed_result = self._attempt_heal(error_event, func, args, kwargs)
                    if healed_result is not None:
                        return healed_result
                
                # If can't heal or healing failed, re-raise
                raise
        
        return wrapper
    
    def _capture_error(self, exception: Exception, func: Callable, args: tuple, kwargs: dict) -> Dict:
        """Capture full error context"""
        
        # Generate error signature (hash of error type + message + location)
        error_signature = self._generate_signature(exception, func)
        
        # Get stack trace
        stack_trace = ''.join(traceback.format_exception(type(exception), exception, exception.__traceback__))
        
        # Build error event
        error_event = {
            'error_id': error_signature,
            'subsystem': self.subsystem_name,
            'function': func.__name__,
            'error_type': type(exception).__name__,
            'message': str(exception),
            'stack_trace': stack_trace,
            'timestamp': datetime.now().isoformat(),
            'args': str(args)[:500],  # Limit size
            'kwargs': str(kwargs)[:500],
            'require_approval': self.require_approval
        }
        
        logger.error(f"[{self.subsystem_name}] Error in {func.__name__}: {exception}")
        
        return error_event
    
    def _generate_signature(self, exception: Exception, func: Callable) -> str:
        """Generate unique signature for this error"""
        sig_string = f"{type(exception).__name__}|{func.__name__}|{str(exception)[:100]}"
        return hashlib.sha256(sig_string.encode()).hexdigest()[:16]
    
    def _attempt_heal(self, error_event: Dict, func: Callable, args: tuple, kwargs: dict) -> Optional[Any]:
        """Attempt to auto-heal the error"""
        
        if not self.error_kb:
            return None
        
        # Check if we've seen this error before
        fix = self.error_kb.get_fix(error_event['error_id'])
        
        if fix:
            logger.info(f"Applying known fix for {error_event['error_id']}")
            try:
                # Apply the fix and retry
                result = self.error_kb.apply_fix(fix, func, args, kwargs)
                logger.info(f"Auto-heal successful for {error_event['error_id']}")
                return result
            except Exception as e:
                logger.error(f"Auto-heal failed: {e}")
                return None
        
        return None


def sentinel(subsystem: str, auto_heal: bool = True, require_approval: bool = False):
    """
    Decorator to wrap functions with error sentinel
    
    Usage:
        @sentinel("KnowledgeEngine", auto_heal=True)
        def my_function():
            ...
    """
    return ErrorSentinel(subsystem, auto_heal, require_approval)


def sentinel_wrap(obj: Any, subsystem: str, auto_heal: bool = True, require_approval: bool = False):
    """
    Wrap an existing object's methods with sentinels
    
    Usage:
        ke = KnowledgeEngine(conn)
        ke = sentinel_wrap(ke, "KnowledgeEngine")
    """
    
    class SentinelWrapper:
        def __init__(self, wrapped_obj):
            self._wrapped = wrapped_obj
            self._sentinel = ErrorSentinel(subsystem, auto_heal, require_approval)
        
        def __getattr__(self, name):
            attr = getattr(self._wrapped, name)
            
            # If it's a callable method, wrap it
            if callable(attr):
                @wraps(attr)
                def wrapped_method(*args, **kwargs):
                    try:
                        return attr(*args, **kwargs)
                    except Exception as e:
                        error_event = self._sentinel._capture_error(e, attr, args, kwargs)
                        get_error_bus().publish(error_event)
                        
                        if auto_heal and not require_approval:
                            healed = self._sentinel._attempt_heal(error_event, attr, args, kwargs)
                            if healed is not None:
                                return healed
                        
                        raise
                
                return wrapped_method
            
            return attr
    
    return SentinelWrapper(obj)
