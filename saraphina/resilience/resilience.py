"""
System Resilience Components
Circuit breaker, rate limiting, health checks, self-healing
"""
import time
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from collections import deque


class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failures detected, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreaker:
    """Circuit breaker pattern implementation"""
    name: str
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    success_threshold: int = 2
    
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float = 0
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                raise Exception(f"Circuit breaker {self.name} is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitState.CLOSED
                print(f"✓ Circuit breaker {self.name} closed (recovered)")
    
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            print(f"⚠️  Circuit breaker {self.name} opened (service degraded)")


class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(self, rate: float, burst: int):
        """
        Args:
            rate: Tokens per second
            burst: Maximum burst size (bucket capacity)
        """
        self.rate = rate
        self.burst = burst
        self.tokens = burst
        self.last_update = time.time()
    
    def allow(self, tokens: int = 1) -> bool:
        """Check if request is allowed"""
        now = time.time()
        elapsed = now - self.last_update
        
        # Refill tokens
        self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
        self.last_update = now
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        
        return False
    
    def wait_time(self) -> float:
        """Get time to wait before retry"""
        if self.tokens >= 1:
            return 0
        return (1 - self.tokens) / self.rate


class SlidingWindowRateLimiter:
    """Sliding window rate limiter (more accurate than token bucket)"""
    
    def __init__(self, max_requests: int, window_seconds: float):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: deque = deque()
    
    def allow(self) -> bool:
        """Check if request is allowed"""
        now = time.time()
        cutoff = now - self.window_seconds
        
        # Remove old requests
        while self.requests and self.requests[0] < cutoff:
            self.requests.popleft()
        
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        
        return False


@dataclass
class HealthCheck:
    """Health check configuration"""
    name: str
    check_func: Callable
    interval_seconds: float = 30.0
    timeout_seconds: float = 5.0
    healthy: bool = True
    last_check: float = 0
    failure_count: int = 0


class HealthMonitor:
    """System health monitoring and self-healing"""
    
    def __init__(self):
        self.checks: Dict[str, HealthCheck] = {}
        self.running = False
    
    def register_check(self, name: str, check_func: Callable, 
                      interval_seconds: float = 30.0):
        """Register health check"""
        self.checks[name] = HealthCheck(
            name=name,
            check_func=check_func,
            interval_seconds=interval_seconds
        )
    
    async def run_checks(self):
        """Run all health checks periodically"""
        self.running = True
        
        while self.running:
            for check in self.checks.values():
                now = time.time()
                
                if now - check.last_check >= check.interval_seconds:
                    await self._run_check(check)
            
            await asyncio.sleep(1)
    
    async def _run_check(self, check: HealthCheck):
        """Run single health check"""
        check.last_check = time.time()
        
        try:
            result = await asyncio.wait_for(
                check.check_func(),
                timeout=check.timeout_seconds
            )
            
            if result:
                if not check.healthy:
                    print(f"✓ Service {check.name} recovered")
                check.healthy = True
                check.failure_count = 0
            else:
                check.healthy = False
                check.failure_count += 1
                print(f"⚠️  Health check failed: {check.name}")
                
        except Exception as e:
            check.healthy = False
            check.failure_count += 1
            print(f"❌ Health check error: {check.name} - {e}")
    
    def get_status(self) -> Dict:
        """Get overall system health status"""
        healthy_count = sum(1 for c in self.checks.values() if c.healthy)
        total_count = len(self.checks)
        
        return {
            "healthy": healthy_count == total_count,
            "healthy_checks": healthy_count,
            "total_checks": total_count,
            "checks": {
                name: {
                    "healthy": check.healthy,
                    "last_check": check.last_check,
                    "failure_count": check.failure_count
                }
                for name, check in self.checks.items()
            }
        }
    
    def stop(self):
        """Stop health monitoring"""
        self.running = False


class AutoScaler:
    """Horizontal auto-scaling manager"""
    
    def __init__(self, min_instances: int = 1, max_instances: int = 10):
        self.min_instances = min_instances
        self.max_instances = max_instances
        self.current_instances = min_instances
        self.metrics_history: deque = deque(maxlen=10)
    
    def record_metrics(self, cpu_percent: float, memory_percent: float, 
                      request_rate: float):
        """Record system metrics"""
        self.metrics_history.append({
            "timestamp": time.time(),
            "cpu": cpu_percent,
            "memory": memory_percent,
            "request_rate": request_rate
        })
    
    def should_scale_up(self) -> bool:
        """Check if should scale up"""
        if len(self.metrics_history) < 3:
            return False
        
        if self.current_instances >= self.max_instances:
            return False
        
        # Check if consistently high load
        recent = list(self.metrics_history)[-3:]
        avg_cpu = sum(m["cpu"] for m in recent) / len(recent)
        avg_memory = sum(m["memory"] for m in recent) / len(recent)
        
        return avg_cpu > 70 or avg_memory > 80
    
    def should_scale_down(self) -> bool:
        """Check if should scale down"""
        if len(self.metrics_history) < 5:
            return False
        
        if self.current_instances <= self.min_instances:
            return False
        
        # Check if consistently low load
        recent = list(self.metrics_history)[-5:]
        avg_cpu = sum(m["cpu"] for m in recent) / len(recent)
        avg_memory = sum(m["memory"] for m in recent) / len(recent)
        
        return avg_cpu < 30 and avg_memory < 40
    
    def scale_up(self):
        """Scale up by one instance"""
        if self.current_instances < self.max_instances:
            self.current_instances += 1
            print(f"⬆️  Scaling up to {self.current_instances} instances")
            # In production: trigger orchestrator (K8s, ECS, etc.)
    
    def scale_down(self):
        """Scale down by one instance"""
        if self.current_instances > self.min_instances:
            self.current_instances -= 1
            print(f"⬇️  Scaling down to {self.current_instances} instances")
            # In production: trigger orchestrator


class RetryPolicy:
    """Exponential backoff retry policy"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, 
                 max_delay: float = 60.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic"""
        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries:
                    raise e
                
                delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                print(f"Retry {attempt + 1}/{self.max_retries} after {delay}s")
                await asyncio.sleep(delay)


# Global resilience components
_circuit_breakers: Dict[str, CircuitBreaker] = {}
_rate_limiters: Dict[str, RateLimiter] = {}
_health_monitor = None

def get_circuit_breaker(name: str, failure_threshold: int = 5) -> CircuitBreaker:
    """Get or create circuit breaker"""
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name, failure_threshold)
    return _circuit_breakers[name]

def get_rate_limiter(name: str, rate: float, burst: int) -> RateLimiter:
    """Get or create rate limiter"""
    if name not in _rate_limiters:
        _rate_limiters[name] = RateLimiter(rate, burst)
    return _rate_limiters[name]

def get_health_monitor() -> HealthMonitor:
    """Get global health monitor"""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = HealthMonitor()
    return _health_monitor
