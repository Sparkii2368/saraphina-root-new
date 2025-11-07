#!/usr/bin/env python3
"""
Contract-Based API Gateway: Formal capability contracts, rate limiting, quota management.
Features: Token bucket algorithm, SLA enforcement, capability negotiation, usage tracking.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import time
import json


class SLATier(Enum):
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


@dataclass
class APIContract:
    """Formal contract defining API capabilities and limits."""
    contract_id: str
    client_id: str
    tier: SLATier
    capabilities: List[str]
    rate_limit: int  # requests per minute
    daily_quota: int
    burst_limit: int
    priority: int = 0
    valid_from: datetime = field(default_factory=datetime.utcnow)
    valid_until: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SLAMetrics:
    """Service Level Agreement metrics."""
    uptime_target: float = 0.99  # 99%
    latency_p95_target_ms: float = 200.0
    error_rate_target: float = 0.01  # 1%
    throughput_target: int = 1000  # requests per second


class TokenBucket:
    """Token bucket algorithm for rate limiting."""
    
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.tokens = float(capacity)
        self.last_refill = time.time()
    
    def consume(self, tokens: int = 1) -> bool:
        """Attempt to consume tokens."""
        self._refill()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def _refill(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        refill_amount = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + refill_amount)
        self.last_refill = now
    
    def get_wait_time(self, tokens: int = 1) -> float:
        """Calculate wait time until tokens available."""
        self._refill()
        if self.tokens >= tokens:
            return 0.0
        deficit = tokens - self.tokens
        return deficit / self.refill_rate


class QuotaManager:
    """Manage daily/monthly quotas."""
    
    def __init__(self):
        self.quotas: Dict[str, Dict[str, Any]] = {}
    
    def set_quota(self, client_id: str, limit: int, period: str = 'daily'):
        """Set quota for client."""
        self.quotas[client_id] = {
            'limit': limit,
            'used': 0,
            'period': period,
            'reset_at': self._calculate_reset_time(period)
        }
    
    def check_quota(self, client_id: str) -> bool:
        """Check if client has quota remaining."""
        if client_id not in self.quotas:
            return True  # No quota restriction
        
        quota = self.quotas[client_id]
        
        # Check if quota needs reset
        if datetime.utcnow() >= quota['reset_at']:
            quota['used'] = 0
            quota['reset_at'] = self._calculate_reset_time(quota['period'])
        
        return quota['used'] < quota['limit']
    
    def consume_quota(self, client_id: str, amount: int = 1) -> bool:
        """Consume quota."""
        if not self.check_quota(client_id):
            return False
        
        if client_id in self.quotas:
            self.quotas[client_id]['used'] += amount
        
        return True
    
    def get_quota_status(self, client_id: str) -> Dict[str, Any]:
        """Get quota status for client."""
        if client_id not in self.quotas:
            return {'unlimited': True}
        
        quota = self.quotas[client_id]
        remaining = quota['limit'] - quota['used']
        
        return {
            'limit': quota['limit'],
            'used': quota['used'],
            'remaining': remaining,
            'reset_at': quota['reset_at'].isoformat(),
            'percentage_used': (quota['used'] / quota['limit'] * 100) if quota['limit'] > 0 else 0
        }
    
    @staticmethod
    def _calculate_reset_time(period: str) -> datetime:
        """Calculate next reset time."""
        now = datetime.utcnow()
        if period == 'daily':
            return (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == 'monthly':
            next_month = now.replace(day=1) + timedelta(days=32)
            return next_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return now + timedelta(hours=1)


class CapabilityRegistry:
    """Registry of available capabilities."""
    
    def __init__(self):
        self.capabilities: Dict[str, Dict[str, Any]] = {}
    
    def register_capability(self, name: str, handler: Callable, 
                          cost: int = 1, min_tier: SLATier = SLATier.FREE):
        """Register API capability."""
        self.capabilities[name] = {
            'handler': handler,
            'cost': cost,
            'min_tier': min_tier,
            'total_calls': 0,
            'total_errors': 0
        }
    
    def can_access(self, capability: str, tier: SLATier) -> bool:
        """Check if tier can access capability."""
        if capability not in self.capabilities:
            return False
        
        cap_info = self.capabilities[capability]
        tier_order = [SLATier.FREE, SLATier.BASIC, SLATier.PREMIUM, SLATier.ENTERPRISE]
        
        required_tier = cap_info['min_tier']
        return tier_order.index(tier) >= tier_order.index(required_tier)
    
    def execute(self, capability: str, *args, **kwargs) -> Any:
        """Execute capability."""
        if capability not in self.capabilities:
            raise ValueError(f"Unknown capability: {capability}")
        
        cap_info = self.capabilities[capability]
        cap_info['total_calls'] += 1
        
        try:
            return cap_info['handler'](*args, **kwargs)
        except Exception as e:
            cap_info['total_errors'] += 1
            raise e
    
    def get_capability_stats(self, capability: str) -> Dict[str, Any]:
        """Get statistics for capability."""
        if capability not in self.capabilities:
            return {}
        
        cap_info = self.capabilities[capability]
        return {
            'total_calls': cap_info['total_calls'],
            'total_errors': cap_info['total_errors'],
            'error_rate': cap_info['total_errors'] / max(cap_info['total_calls'], 1),
            'min_tier': cap_info['min_tier'].value
        }


class SLAMonitor:
    """Monitor and enforce SLA compliance."""
    
    def __init__(self, metrics: SLAMetrics):
        self.metrics = metrics
        self.requests: List[Dict[str, Any]] = []
        self.window_size = 1000
    
    def record_request(self, success: bool, latency_ms: float):
        """Record API request."""
        self.requests.append({
            'success': success,
            'latency_ms': latency_ms,
            'timestamp': datetime.utcnow()
        })
        
        # Keep only recent requests
        if len(self.requests) > self.window_size:
            self.requests = self.requests[-self.window_size:]
    
    def get_compliance_report(self) -> Dict[str, Any]:
        """Generate SLA compliance report."""
        if not self.requests:
            return {'status': 'insufficient_data'}
        
        # Calculate metrics
        total = len(self.requests)
        successful = sum(1 for r in self.requests if r['success'])
        uptime = successful / total
        
        latencies = [r['latency_ms'] for r in self.requests]
        latencies.sort()
        p95_index = int(len(latencies) * 0.95)
        p95_latency = latencies[p95_index] if latencies else 0
        
        error_rate = (total - successful) / total
        
        # Check compliance
        uptime_ok = uptime >= self.metrics.uptime_target
        latency_ok = p95_latency <= self.metrics.latency_p95_target_ms
        error_rate_ok = error_rate <= self.metrics.error_rate_target
        
        return {
            'status': 'compliant' if (uptime_ok and latency_ok and error_rate_ok) else 'violation',
            'uptime': {'actual': uptime, 'target': self.metrics.uptime_target, 'ok': uptime_ok},
            'latency_p95_ms': {'actual': p95_latency, 'target': self.metrics.latency_p95_target_ms, 'ok': latency_ok},
            'error_rate': {'actual': error_rate, 'target': self.metrics.error_rate_target, 'ok': error_rate_ok},
            'sample_size': total
        }


class APIGateway:
    """Main API gateway orchestrator."""
    
    def __init__(self, conn):
        self.conn = conn
        self.contracts: Dict[str, APIContract] = {}
        self.token_buckets: Dict[str, TokenBucket] = {}
        self.quota_manager = QuotaManager()
        self.capability_registry = CapabilityRegistry()
        self.sla_monitor = SLAMonitor(SLAMetrics())
        self._init_db()
    
    def _init_db(self):
        cur = self.conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS api_contracts (
                contract_id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                tier TEXT NOT NULL,
                capabilities TEXT NOT NULL,
                rate_limit INTEGER NOT NULL,
                daily_quota INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS api_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT NOT NULL,
                capability TEXT NOT NULL,
                success BOOLEAN NOT NULL,
                latency_ms REAL NOT NULL,
                timestamp TEXT NOT NULL
            )
        ''')
        self.conn.commit()
    
    def register_contract(self, contract: APIContract):
        """Register API contract."""
        self.contracts[contract.client_id] = contract
        
        # Setup rate limiter
        self.token_buckets[contract.client_id] = TokenBucket(
            capacity=contract.burst_limit,
            refill_rate=contract.rate_limit / 60.0  # per second
        )
        
        # Setup quota
        self.quota_manager.set_quota(contract.client_id, contract.daily_quota)
        
        # Store in database
        cur = self.conn.cursor()
        cur.execute('''
            INSERT OR REPLACE INTO api_contracts 
            (contract_id, client_id, tier, capabilities, rate_limit, daily_quota, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            contract.contract_id,
            contract.client_id,
            contract.tier.value,
            json.dumps(contract.capabilities),
            contract.rate_limit,
            contract.daily_quota,
            datetime.utcnow().isoformat()
        ))
        self.conn.commit()
    
    def request(self, client_id: str, capability: str, *args, **kwargs) -> Dict[str, Any]:
        """Process API request."""
        start_time = time.time()
        
        # Check contract exists
        if client_id not in self.contracts:
            return {
                'success': False,
                'error': 'no_contract',
                'message': 'No valid contract found'
            }
        
        contract = self.contracts[client_id]
        
        # Check capability access
        if not self.capability_registry.can_access(capability, contract.tier):
            return {
                'success': False,
                'error': 'capability_denied',
                'message': f'Tier {contract.tier.value} cannot access {capability}'
            }
        
        # Check rate limit
        if not self.token_buckets[client_id].consume():
            wait_time = self.token_buckets[client_id].get_wait_time()
            return {
                'success': False,
                'error': 'rate_limit_exceeded',
                'retry_after': wait_time
            }
        
        # Check quota
        if not self.quota_manager.check_quota(client_id):
            quota_status = self.quota_manager.get_quota_status(client_id)
            return {
                'success': False,
                'error': 'quota_exceeded',
                'quota_status': quota_status
            }
        
        # Execute capability
        try:
            result = self.capability_registry.execute(capability, *args, **kwargs)
            self.quota_manager.consume_quota(client_id)
            
            latency_ms = (time.time() - start_time) * 1000
            self.sla_monitor.record_request(True, latency_ms)
            self._log_request(client_id, capability, True, latency_ms)
            
            return {
                'success': True,
                'result': result,
                'latency_ms': latency_ms
            }
        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            self.sla_monitor.record_request(False, latency_ms)
            self._log_request(client_id, capability, False, latency_ms)
            
            return {
                'success': False,
                'error': 'execution_failed',
                'message': str(e),
                'latency_ms': latency_ms
            }
    
    def get_client_status(self, client_id: str) -> Dict[str, Any]:
        """Get comprehensive client status."""
        if client_id not in self.contracts:
            return {'error': 'no_contract'}
        
        contract = self.contracts[client_id]
        bucket = self.token_buckets[client_id]
        quota_status = self.quota_manager.get_quota_status(client_id)
        
        return {
            'client_id': client_id,
            'tier': contract.tier.value,
            'capabilities': contract.capabilities,
            'rate_limit': {
                'tokens_available': int(bucket.tokens),
                'capacity': bucket.capacity,
                'refill_rate_per_min': contract.rate_limit
            },
            'quota': quota_status
        }
    
    def negotiate_upgrade(self, client_id: str, target_tier: SLATier) -> Dict[str, Any]:
        """Negotiate contract upgrade."""
        if client_id not in self.contracts:
            return {'success': False, 'error': 'no_contract'}
        
        current_contract = self.contracts[client_id]
        
        # Define tier specifications
        tier_specs = {
            SLATier.FREE: {'rate': 10, 'quota': 100, 'burst': 15},
            SLATier.BASIC: {'rate': 60, 'quota': 5000, 'burst': 100},
            SLATier.PREMIUM: {'rate': 300, 'quota': 50000, 'burst': 500},
            SLATier.ENTERPRISE: {'rate': 1000, 'quota': 1000000, 'burst': 2000}
        }
        
        if target_tier not in tier_specs:
            return {'success': False, 'error': 'invalid_tier'}
        
        specs = tier_specs[target_tier]
        
        # Create upgraded contract
        new_contract = APIContract(
            contract_id=f"{current_contract.contract_id}_upgraded",
            client_id=client_id,
            tier=target_tier,
            capabilities=current_contract.capabilities,
            rate_limit=specs['rate'],
            daily_quota=specs['quota'],
            burst_limit=specs['burst']
        )
        
        return {
            'success': True,
            'new_contract': {
                'tier': target_tier.value,
                'rate_limit': specs['rate'],
                'daily_quota': specs['quota'],
                'burst_limit': specs['burst']
            }
        }
    
    def get_sla_report(self) -> Dict[str, Any]:
        """Get SLA compliance report."""
        return self.sla_monitor.get_compliance_report()
    
    def _log_request(self, client_id: str, capability: str, success: bool, latency_ms: float):
        """Log API request."""
        cur = self.conn.cursor()
        cur.execute('''
            INSERT INTO api_requests (client_id, capability, success, latency_ms, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (client_id, capability, success, latency_ms, datetime.utcnow().isoformat()))
        self.conn.commit()
    
    def get_usage_statistics(self, client_id: Optional[str] = None) -> Dict[str, Any]:
        """Get usage statistics."""
        cur = self.conn.cursor()
        
        if client_id:
            cur.execute('''
                SELECT capability, COUNT(*), AVG(latency_ms), SUM(CASE WHEN success THEN 1 ELSE 0 END)
                FROM api_requests
                WHERE client_id = ?
                GROUP BY capability
            ''', (client_id,))
        else:
            cur.execute('''
                SELECT client_id, COUNT(*), AVG(latency_ms), SUM(CASE WHEN success THEN 1 ELSE 0 END)
                FROM api_requests
                GROUP BY client_id
            ''')
        
        stats = []
        for row in cur.fetchall():
            stats.append({
                'identifier': row[0],
                'total_requests': row[1],
                'avg_latency_ms': row[2],
                'successful_requests': row[3],
                'success_rate': row[3] / row[1] if row[1] > 0 else 0
            })
        
        return {'statistics': stats}
