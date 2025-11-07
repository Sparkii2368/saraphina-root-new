#!/usr/bin/env python3
"""
Self-Optimization Pipeline: Autonomous hyperparameter tuning, model retraining, A/B testing.
Features: Bayesian optimization, performance tracking, auto-scaling, adaptive learning rates.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
import json
import random
import math
from collections import defaultdict


class BayesianOptimizer:
    """Bayesian optimization for hyperparameter search using Gaussian Process surrogate."""
    
    def __init__(self, param_space: Dict[str, tuple], acquisition: str = 'ucb'):
        self.param_space = param_space  # {'param': (min, max)}
        self.acquisition = acquisition  # 'ucb', 'ei', 'poi'
        self.observations: List[tuple] = []  # [(params, score)]
        self.best_score = -float('inf')
        self.best_params = None
        
    def suggest(self) -> Dict[str, float]:
        """Suggest next hyperparameter configuration using acquisition function."""
        if len(self.observations) < 3:
            # Random exploration phase
            return {k: random.uniform(v[0], v[1]) for k, v in self.param_space.items()}
        
        # Build simple GP surrogate (mean and uncertainty)
        candidates = []
        for _ in range(100):
            params = {k: random.uniform(v[0], v[1]) for k, v in self.param_space.items()}
            mu, sigma = self._gp_predict(params)
            
            if self.acquisition == 'ucb':
                score = mu + 2.0 * sigma  # Upper confidence bound
            elif self.acquisition == 'ei':
                score = self._expected_improvement(mu, sigma)
            else:  # poi
                score = self._probability_of_improvement(mu, sigma)
                
            candidates.append((score, params))
        
        return max(candidates, key=lambda x: x[0])[1]
    
    def observe(self, params: Dict[str, float], score: float):
        """Record observation from hyperparameter evaluation."""
        self.observations.append((params, score))
        if score > self.best_score:
            self.best_score = score
            self.best_params = params
    
    def _gp_predict(self, params: Dict[str, float]) -> tuple[float, float]:
        """Simple GP prediction: weighted average by similarity."""
        if not self.observations:
            return 0.0, 1.0
        
        weights = []
        scores = []
        for obs_params, obs_score in self.observations:
            dist = sum((params[k] - obs_params[k])**2 for k in params) ** 0.5
            weight = math.exp(-dist)
            weights.append(weight)
            scores.append(obs_score)
        
        total_weight = sum(weights)
        mu = sum(w * s for w, s in zip(weights, scores)) / total_weight if total_weight > 0 else 0.0
        sigma = 1.0 / (1.0 + len(self.observations))  # Decreasing uncertainty
        return mu, sigma
    
    def _expected_improvement(self, mu: float, sigma: float) -> float:
        """Expected improvement acquisition."""
        if sigma == 0:
            return 0.0
        z = (mu - self.best_score) / sigma
        return (mu - self.best_score) * self._normal_cdf(z) + sigma * self._normal_pdf(z)
    
    def _probability_of_improvement(self, mu: float, sigma: float) -> float:
        """Probability of improvement acquisition."""
        if sigma == 0:
            return 0.0
        z = (mu - self.best_score) / sigma
        return self._normal_cdf(z)
    
    @staticmethod
    def _normal_cdf(x: float) -> float:
        """Cumulative distribution function for standard normal."""
        return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0
    
    @staticmethod
    def _normal_pdf(x: float) -> float:
        """Probability density function for standard normal."""
        return math.exp(-x**2 / 2.0) / math.sqrt(2.0 * math.pi)


class ABTester:
    """A/B testing framework with statistical significance testing."""
    
    def __init__(self, variants: List[str], alpha: float = 0.05):
        self.variants = variants
        self.alpha = alpha
        self.results: Dict[str, List[float]] = {v: [] for v in variants}
        
    def record(self, variant: str, outcome: float):
        """Record outcome for variant."""
        if variant in self.results:
            self.results[variant].append(outcome)
    
    def get_winner(self) -> Optional[str]:
        """Determine winning variant using t-test."""
        if any(len(v) < 10 for v in self.results.values()):
            return None  # Not enough data
        
        means = {v: sum(outcomes) / len(outcomes) for v, outcomes in self.results.items()}
        best_variant = max(means, key=means.get)
        
        # Simple two-sample t-test against others
        best_outcomes = self.results[best_variant]
        for variant, outcomes in self.results.items():
            if variant == best_variant:
                continue
            
            if not self._is_significantly_better(best_outcomes, outcomes):
                return None  # No clear winner
        
        return best_variant
    
    def _is_significantly_better(self, a: List[float], b: List[float]) -> bool:
        """Check if sample a is significantly better than b."""
        mean_a = sum(a) / len(a)
        mean_b = sum(b) / len(b)
        
        if mean_a <= mean_b:
            return False
        
        var_a = sum((x - mean_a)**2 for x in a) / len(a)
        var_b = sum((x - mean_b)**2 for x in b) / len(b)
        
        pooled_std = math.sqrt((var_a / len(a)) + (var_b / len(b)))
        if pooled_std == 0:
            return True
        
        t_stat = (mean_a - mean_b) / pooled_std
        # Simplified: use threshold instead of full t-distribution
        return t_stat > 2.0  # Roughly p < 0.05 for reasonable n


class MetricsTracker:
    """Performance metrics tracking with rolling windows and anomaly detection."""
    
    def __init__(self, conn, window_size: int = 100):
        self.conn = conn
        self.window_size = window_size
        self.metrics: Dict[str, List[tuple]] = defaultdict(list)  # {metric: [(timestamp, value)]}
        self._init_db()
    
    def _init_db(self):
        cur = self.conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS optimization_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT NOT NULL,
                value REAL NOT NULL,
                timestamp TEXT NOT NULL,
                metadata TEXT
            )
        ''')
        self.conn.commit()
    
    def record(self, metric_name: str, value: float, metadata: Optional[Dict] = None):
        """Record metric value."""
        timestamp = datetime.utcnow().isoformat()
        
        # In-memory
        self.metrics[metric_name].append((timestamp, value))
        if len(self.metrics[metric_name]) > self.window_size:
            self.metrics[metric_name].pop(0)
        
        # Persistent
        cur = self.conn.cursor()
        cur.execute(
            'INSERT INTO optimization_metrics (metric_name, value, timestamp, metadata) VALUES (?, ?, ?, ?)',
            (metric_name, value, timestamp, json.dumps(metadata) if metadata else None)
        )
        self.conn.commit()
    
    def get_statistics(self, metric_name: str) -> Dict[str, float]:
        """Get statistical summary of metric."""
        if metric_name not in self.metrics or not self.metrics[metric_name]:
            return {}
        
        values = [v for _, v in self.metrics[metric_name]]
        n = len(values)
        mean = sum(values) / n
        variance = sum((x - mean)**2 for x in values) / n
        std = math.sqrt(variance)
        
        sorted_values = sorted(values)
        return {
            'mean': mean,
            'std': std,
            'min': sorted_values[0],
            'max': sorted_values[-1],
            'median': sorted_values[n // 2],
            'p95': sorted_values[int(n * 0.95)] if n > 20 else sorted_values[-1],
            'count': n
        }
    
    def detect_anomaly(self, metric_name: str, threshold_std: float = 3.0) -> bool:
        """Detect if latest value is anomalous."""
        if metric_name not in self.metrics or len(self.metrics[metric_name]) < 10:
            return False
        
        values = [v for _, v in self.metrics[metric_name][:-1]]
        latest = self.metrics[metric_name][-1][1]
        
        mean = sum(values) / len(values)
        std = math.sqrt(sum((x - mean)**2 for x in values) / len(values))
        
        return abs(latest - mean) > threshold_std * std if std > 0 else False


class SelfOptimizer:
    """Orchestrates self-optimization: hyperparameter tuning, A/B testing, adaptive learning."""
    
    def __init__(self, conn, objective_fn: Optional[Callable] = None):
        self.conn = conn
        self.objective_fn = objective_fn or self._default_objective
        self.metrics = MetricsTracker(conn)
        self.optimizers: Dict[str, BayesianOptimizer] = {}
        self.ab_tests: Dict[str, ABTester] = {}
        self.config: Dict[str, Any] = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load optimization configuration."""
        cur = self.conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS optimization_config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        cur.execute('SELECT key, value FROM optimization_config')
        return {row[0]: json.loads(row[1]) for row in cur.fetchall()}
    
    def _save_config(self):
        """Persist optimization configuration."""
        cur = self.conn.cursor()
        for key, value in self.config.items():
            cur.execute(
                'INSERT OR REPLACE INTO optimization_config (key, value, updated_at) VALUES (?, ?, ?)',
                (key, json.dumps(value), datetime.utcnow().isoformat())
            )
        self.conn.commit()
    
    def optimize_hyperparameters(self, component: str, param_space: Dict[str, tuple], n_iterations: int = 50) -> Dict[str, float]:
        """Run Bayesian optimization for component hyperparameters."""
        if component not in self.optimizers:
            self.optimizers[component] = BayesianOptimizer(param_space)
        
        optimizer = self.optimizers[component]
        
        for i in range(n_iterations):
            params = optimizer.suggest()
            score = self.objective_fn(component, params)
            optimizer.observe(params, score)
            self.metrics.record(f'{component}_optimization_score', score, {'iteration': i, 'params': params})
        
        # Store best config
        if optimizer.best_params:
            self.config[f'{component}_params'] = optimizer.best_params
            self._save_config()
        
        return optimizer.best_params or {}
    
    def run_ab_test(self, experiment: str, variants: List[str], duration_hours: int = 24) -> Optional[str]:
        """Run A/B test and return winning variant."""
        if experiment not in self.ab_tests:
            self.ab_tests[experiment] = ABTester(variants)
        
        # In production, this would be called continuously
        # Here we simulate by checking existing metrics
        tester = self.ab_tests[experiment]
        winner = tester.get_winner()
        
        if winner:
            self.config[f'ab_test_{experiment}_winner'] = winner
            self._save_config()
        
        return winner
    
    def adaptive_learning_rate(self, current_lr: float, loss_history: List[float]) -> float:
        """Adapt learning rate based on loss trajectory."""
        if len(loss_history) < 5:
            return current_lr
        
        recent_losses = loss_history[-5:]
        
        # Check if improving
        if all(recent_losses[i] > recent_losses[i+1] for i in range(len(recent_losses)-1)):
            # Consistently improving: increase LR
            return min(current_lr * 1.1, 1e-2)
        elif all(recent_losses[i] < recent_losses[i+1] for i in range(len(recent_losses)-1)):
            # Diverging: decrease LR
            return max(current_lr * 0.5, 1e-6)
        else:
            # Oscillating: slight decrease
            return current_lr * 0.9
    
    def auto_scale_resources(self, workload_metric: str, target_utilization: float = 0.7) -> Dict[str, Any]:
        """Recommend resource scaling based on workload."""
        stats = self.metrics.get_statistics(workload_metric)
        if not stats:
            return {'action': 'maintain', 'reason': 'insufficient_data'}
        
        current_utilization = stats['p95']
        
        if current_utilization > target_utilization * 1.3:
            scale_factor = math.ceil(current_utilization / target_utilization)
            return {'action': 'scale_up', 'factor': scale_factor, 'reason': 'high_utilization'}
        elif current_utilization < target_utilization * 0.5:
            scale_factor = max(0.5, current_utilization / target_utilization)
            return {'action': 'scale_down', 'factor': scale_factor, 'reason': 'low_utilization'}
        
        return {'action': 'maintain', 'reason': 'optimal_utilization'}
    
    def _default_objective(self, component: str, params: Dict[str, float]) -> float:
        """Default objective function (maximize)."""
        # Placeholder: return random score + small bias from params
        return random.random() + sum(params.values()) * 0.01
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive optimization report."""
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'optimizers': {},
            'ab_tests': {},
            'metrics': {}
        }
        
        for component, optimizer in self.optimizers.items():
            report['optimizers'][component] = {
                'best_score': optimizer.best_score,
                'best_params': optimizer.best_params,
                'iterations': len(optimizer.observations)
            }
        
        for experiment, tester in self.ab_tests.items():
            winner = tester.get_winner()
            report['ab_tests'][experiment] = {
                'winner': winner,
                'variants': list(tester.results.keys()),
                'sample_sizes': {v: len(outcomes) for v, outcomes in tester.results.items()}
            }
        
        for metric_name in self.metrics.metrics:
            report['metrics'][metric_name] = self.metrics.get_statistics(metric_name)
        
        return report
