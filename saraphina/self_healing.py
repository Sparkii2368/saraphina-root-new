#!/usr/bin/env python3
"""
Self-Healing System: Automatic error detection, recovery, circuit breakers, chaos engineering.
Features: Health monitoring, automatic rollback, retry policies, bulkheads, adaptive recovery.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional, Callable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import time
import random
import json
import traceback


class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class HealthCheck:
    """Health check configuration."""
    check_id: str
    check_fn: Callable[[], bool]
    interval_seconds: float = 30.0
    timeout_seconds: float = 5.0
    failure_threshold: int = 3
    last_check: Optional[datetime] = None
    consecutive_failures: int = 0
    healthy: bool = True


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    failure_threshold: int = 5
    success_threshold: int = 2
    timeout_seconds: float = 60.0
    half_open_max_calls: int = 3


class CircuitBreaker:
    """Circuit breaker pattern for fault tolerance."""
    
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.half_open_calls = 0
        self.metrics = {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'rejected_calls': 0
        }
    
    def call(self, fn: Callable, *args, **kwargs) -> Tuple[bool, Any]:
        """Execute function with circuit breaker protection."""
        self.metrics['total_calls'] += 1
        
        # Check if circuit is open
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
            else:
                self.metrics['rejected_calls'] += 1
                return False, Exception(f"Circuit breaker {self.name} is OPEN")
        
        # Limit calls in half-open state
        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_calls >= self.config.half_open_max_calls:
                self.metrics['rejected_calls'] += 1
                return False, Exception(f"Circuit breaker {self.name} half-open limit reached")
            self.half_open_calls += 1
        
        # Execute function
        try:
            result = fn(*args, **kwargs)
            self._on_success()
            return True, result
        except Exception as e:
            self._on_failure()
            return False, e
    
    def _on_success(self):
        """Handle successful call."""
        self.metrics['successful_calls'] += 1
        self.failure_count = 0
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self.success_count = 0
    
    def _on_failure(self):
        """Handle failed call."""
        self.metrics['failed_calls'] += 1
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN
    
    def _should_attempt_reset(self) -> bool:
        """Check if should try to reset from open state."""
        if self.last_failure_time is None:
            return True
        elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
        return elapsed >= self.config.timeout_seconds
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get circuit breaker metrics."""
        return {
            'name': self.name,
            'state': self.state.value,
            'metrics': self.metrics,
            'failure_count': self.failure_count,
            'success_count': self.success_count
        }


class RetryPolicy:
    """Configurable retry policy with backoff."""
    
    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0, 
                 max_delay: float = 60.0, exponential: bool = True,
                 jitter: bool = True):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential = exponential
        self.jitter = jitter
    
    def execute(self, fn: Callable, *args, **kwargs) -> Tuple[bool, Any]:
        """Execute function with retries."""
        last_exception = None
        
        for attempt in range(self.max_attempts):
            try:
                result = fn(*args, **kwargs)
                return True, result
            except Exception as e:
                last_exception = e
                
                if attempt < self.max_attempts - 1:
                    delay = self._calculate_delay(attempt)
                    time.sleep(delay)
        
        return False, last_exception
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and jitter."""
        if self.exponential:
            delay = min(self.base_delay * (2 ** attempt), self.max_delay)
        else:
            delay = self.base_delay
        
        if self.jitter:
            delay *= random.uniform(0.5, 1.5)
        
        return delay


class Snapshot:
    """System state snapshot for rollback."""
    
    def __init__(self, snapshot_id: str, state: Dict[str, Any]):
        self.snapshot_id = snapshot_id
        self.state = state
        self.timestamp = datetime.utcnow()
        self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'snapshot_id': self.snapshot_id,
            'state': self.state,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }


class RollbackManager:
    """Manage state snapshots and rollbacks."""
    
    def __init__(self, max_snapshots: int = 10):
        self.max_snapshots = max_snapshots
        self.snapshots: deque[Snapshot] = deque(maxlen=max_snapshots)
        self.current_state: Optional[Dict[str, Any]] = None
    
    def create_snapshot(self, state: Dict[str, Any]) -> str:
        """Create state snapshot."""
        snapshot_id = f"snap_{datetime.utcnow().timestamp()}"
        snapshot = Snapshot(snapshot_id, state.copy())
        self.snapshots.append(snapshot)
        self.current_state = state
        return snapshot_id
    
    def rollback(self, snapshot_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Rollback to specific snapshot or most recent."""
        if not self.snapshots:
            return None
        
        if snapshot_id:
            snapshot = next((s for s in self.snapshots if s.snapshot_id == snapshot_id), None)
        else:
            snapshot = self.snapshots[-1]
        
        if snapshot:
            self.current_state = snapshot.state.copy()
            return self.current_state
        
        return None
    
    def list_snapshots(self) -> List[Dict[str, Any]]:
        """List all snapshots."""
        return [s.to_dict() for s in self.snapshots]


class HealthMonitor:
    """Continuous health monitoring system."""
    
    def __init__(self):
        self.checks: Dict[str, HealthCheck] = {}
        self.alerts: List[Dict[str, Any]] = []
    
    def register_check(self, check: HealthCheck):
        """Register health check."""
        self.checks[check.check_id] = check
    
    def run_checks(self) -> Dict[str, bool]:
        """Run all health checks."""
        results = {}
        now = datetime.utcnow()
        
        for check_id, check in self.checks.items():
            # Skip if not time yet
            if check.last_check:
                elapsed = (now - check.last_check).total_seconds()
                if elapsed < check.interval_seconds:
                    results[check_id] = check.healthy
                    continue
            
            # Run check
            try:
                check.last_check = now
                is_healthy = check.check_fn()
                
                if is_healthy:
                    check.consecutive_failures = 0
                    check.healthy = True
                else:
                    check.consecutive_failures += 1
                    if check.consecutive_failures >= check.failure_threshold:
                        check.healthy = False
                        self._create_alert(check_id, "Health check failed")
                
                results[check_id] = check.healthy
            
            except Exception as e:
                check.consecutive_failures += 1
                if check.consecutive_failures >= check.failure_threshold:
                    check.healthy = False
                    self._create_alert(check_id, f"Health check exception: {str(e)}")
                results[check_id] = False
        
        return results
    
    def _create_alert(self, check_id: str, message: str):
        """Create health alert."""
        alert = {
            'check_id': check_id,
            'message': message,
            'timestamp': datetime.utcnow().isoformat(),
            'severity': 'critical'
        }
        self.alerts.append(alert)
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health."""
        total = len(self.checks)
        healthy = sum(1 for c in self.checks.values() if c.healthy)
        
        return {
            'overall_status': 'healthy' if healthy == total else 'degraded' if healthy > 0 else 'unhealthy',
            'healthy_checks': healthy,
            'total_checks': total,
            'health_percentage': (healthy / total * 100) if total > 0 else 0,
            'recent_alerts': self.alerts[-10:]
        }


class RecoveryStrategy:
    """Define recovery actions for failures."""
    
    def __init__(self, name: str, strategy_fn: Callable[[Dict[str, Any]], bool]):
        self.name = name
        self.strategy_fn = strategy_fn
        self.execution_count = 0
        self.success_count = 0
    
    def execute(self, context: Dict[str, Any]) -> bool:
        """Execute recovery strategy."""
        self.execution_count += 1
        try:
            success = self.strategy_fn(context)
            if success:
                self.success_count += 1
            return success
        except Exception:
            return False


class ChaosEngineer:
    """Chaos engineering for resilience testing."""
    
    def __init__(self):
        self.experiments: List[Dict[str, Any]] = []
        self.active = False
    
    def inject_latency(self, delay_ms: float):
        """Inject artificial latency."""
        time.sleep(delay_ms / 1000.0)
    
    def inject_error(self, error_rate: float = 0.1) -> bool:
        """Randomly inject errors."""
        return random.random() < error_rate
    
    def inject_timeout(self):
        """Simulate timeout."""
        time.sleep(999)  # Long delay
    
    def run_experiment(self, name: str, target_fn: Callable, 
                      chaos_type: str = 'error', intensity: float = 0.1) -> Dict[str, Any]:
        """Run chaos experiment."""
        experiment = {
            'name': name,
            'chaos_type': chaos_type,
            'intensity': intensity,
            'start_time': datetime.utcnow().isoformat(),
            'results': []
        }
        
        # Execute with chaos
        for i in range(10):
            try:
                if chaos_type == 'latency':
                    self.inject_latency(intensity * 1000)
                elif chaos_type == 'error' and self.inject_error(intensity):
                    raise Exception("Chaos-injected error")
                
                result = target_fn()
                experiment['results'].append({'success': True, 'iteration': i})
            except Exception as e:
                experiment['results'].append({'success': False, 'iteration': i, 'error': str(e)})
        
        experiment['end_time'] = datetime.utcnow().isoformat()
        experiment['success_rate'] = sum(1 for r in experiment['results'] if r['success']) / len(experiment['results'])
        self.experiments.append(experiment)
        
        return experiment


class SelfHealingSystem:
    """Orchestrate self-healing capabilities."""
    
    def __init__(self, conn):
        self.conn = conn
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.health_monitor = HealthMonitor()
        self.rollback_manager = RollbackManager()
        self.recovery_strategies: Dict[str, RecoveryStrategy] = {}
        self.chaos = ChaosEngineer()
        self._init_db()
    
    def _init_db(self):
        cur = self.conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS healing_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                component TEXT NOT NULL,
                description TEXT,
                action_taken TEXT,
                success BOOLEAN,
                timestamp TEXT NOT NULL
            )
        ''')
        self.conn.commit()
    
    def register_circuit_breaker(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """Register circuit breaker."""
        cb = CircuitBreaker(name, config)
        self.circuit_breakers[name] = cb
        return cb
    
    def register_recovery_strategy(self, name: str, strategy: RecoveryStrategy):
        """Register recovery strategy."""
        self.recovery_strategies[name] = strategy
    
    def execute_protected(self, component: str, fn: Callable, *args, **kwargs) -> Tuple[bool, Any]:
        """Execute function with full protection: circuit breaker + retry."""
        if component not in self.circuit_breakers:
            self.register_circuit_breaker(component)
        
        cb = self.circuit_breakers[component]
        retry = RetryPolicy(max_attempts=3)
        
        # Try with circuit breaker and retry
        success, result = retry.execute(lambda: cb.call(fn, *args, **kwargs))
        
        if not success:
            # Attempt recovery
            self._attempt_recovery(component, result)
        
        return success, result
    
    def _attempt_recovery(self, component: str, error: Any):
        """Attempt automatic recovery."""
        context = {
            'component': component,
            'error': str(error),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        for strategy_name, strategy in self.recovery_strategies.items():
            if strategy.execute(context):
                self._log_healing_event('recovery', component, f"Applied {strategy_name}", True)
                return True
        
        # Last resort: rollback
        if self.rollback_manager.rollback():
            self._log_healing_event('rollback', component, "Rolled back to previous state", True)
            return True
        
        self._log_healing_event('recovery_failed', component, "All recovery attempts failed", False)
        return False
    
    def _log_healing_event(self, event_type: str, component: str, description: str, success: bool):
        """Log healing event."""
        cur = self.conn.cursor()
        cur.execute('''
            INSERT INTO healing_events (event_type, component, description, action_taken, success, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (event_type, component, description, event_type, success, datetime.utcnow().isoformat()))
        self.conn.commit()
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        return {
            'health': self.health_monitor.get_system_health(),
            'circuit_breakers': {name: cb.get_metrics() for name, cb in self.circuit_breakers.items()},
            'snapshots': len(self.rollback_manager.snapshots),
            'recovery_strategies': {
                name: {'executions': s.execution_count, 'successes': s.success_count}
                for name, s in self.recovery_strategies.items()
            },
            'chaos_experiments': len(self.chaos.experiments)
        }
