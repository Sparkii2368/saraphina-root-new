#!/usr/bin/env python3
"""
Meta-Optimizer: Analyzes learning patterns, detects stagnation/bias, proposes optimizations.
Features: Strategy analysis, bias detection, automatic parameter tuning, growth tracking.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

from .learning_journal import LearningJournal, LearningEvent, StrategyOutcome


@dataclass
class OptimizationProposal:
    """Proposed optimization with rationale."""
    proposal_id: str
    category: str  # parameter, strategy, architecture
    target: str
    current_value: Any
    proposed_value: Any
    rationale: str
    expected_improvement: float
    confidence: float
    priority: str  # low, medium, high, critical


class StagnationDetector:
    """Detect learning stagnation and plateaus."""
    
    @staticmethod
    def detect_plateau(timeline: List[Tuple[datetime, float]], 
                      threshold: float = 0.05) -> Optional[Dict[str, Any]]:
        """Detect if metric has plateaued."""
        if len(timeline) < 10:
            return None
        
        # Check recent trend
        recent_values = [v for _, v in timeline[-10:]]
        
        # Calculate variance
        mean = sum(recent_values) / len(recent_values)
        variance = sum((x - mean) ** 2 for x in recent_values) / len(recent_values)
        std_dev = variance ** 0.5
        
        # Plateau if low variance
        if std_dev < threshold:
            return {
                'detected': True,
                'mean_value': mean,
                'variance': variance,
                'duration_points': len(recent_values)
            }
        
        return None
    
    @staticmethod
    def detect_decline(timeline: List[Tuple[datetime, float]]) -> Optional[Dict[str, Any]]:
        """Detect declining performance."""
        if len(timeline) < 5:
            return None
        
        recent = [v for _, v in timeline[-5:]]
        older = [v for _, v in timeline[-10:-5]] if len(timeline) >= 10 else [v for _, v in timeline[:-5]]
        
        if not older:
            return None
        
        recent_avg = sum(recent) / len(recent)
        older_avg = sum(older) / len(older)
        
        decline_pct = (older_avg - recent_avg) / older_avg if older_avg > 0 else 0
        
        if decline_pct > 0.1:  # 10% decline
            return {
                'detected': True,
                'decline_percentage': decline_pct,
                'recent_avg': recent_avg,
                'older_avg': older_avg
            }
        
        return None


class BiasDetector:
    """Detect biases in learning strategies."""
    
    @staticmethod
    def detect_overreliance(strategy_performance: Dict[str, StrategyOutcome]) -> List[Dict[str, Any]]:
        """Detect overreliance on specific strategies."""
        if not strategy_performance:
            return []
        
        total_uses = sum(s.total_uses for s in strategy_performance.values())
        biases = []
        
        for name, outcome in strategy_performance.items():
            usage_percentage = outcome.total_uses / total_uses if total_uses > 0 else 0
            
            # Overreliance if >50% of all uses
            if usage_percentage > 0.5:
                biases.append({
                    'type': 'overreliance',
                    'strategy': name,
                    'usage_percentage': usage_percentage,
                    'recommendation': f'Explore alternative strategies to {name}'
                })
        
        return biases
    
    @staticmethod
    def detect_underperforming(strategy_performance: Dict[str, StrategyOutcome], 
                               threshold: float = 0.5) -> List[Dict[str, Any]]:
        """Detect consistently underperforming strategies."""
        underperforming = []
        
        for name, outcome in strategy_performance.items():
            if outcome.total_uses >= 10:  # Minimum sample size
                success_rate = outcome.success_rate()
                
                if success_rate < threshold:
                    underperforming.append({
                        'type': 'underperforming',
                        'strategy': name,
                        'success_rate': success_rate,
                        'total_uses': outcome.total_uses,
                        'recommendation': f'Consider retiring or refining {name}'
                    })
        
        return underperforming
    
    @staticmethod
    def detect_confirmation_bias(events: List[LearningEvent]) -> Optional[Dict[str, Any]]:
        """Detect confirmation bias in feedback handling."""
        if len(events) < 20:
            return None
        
        # Check if positive feedback is overweighted
        positive_feedback = [e for e in events if e.feedback and e.feedback.get('sentiment') == 'positive']
        negative_feedback = [e for e in events if e.feedback and e.feedback.get('sentiment') == 'negative']
        
        if len(negative_feedback) > 0:
            ratio = len(positive_feedback) / len(negative_feedback)
            
            if ratio > 5:  # Much more positive than negative
                return {
                    'detected': True,
                    'positive_count': len(positive_feedback),
                    'negative_count': len(negative_feedback),
                    'ratio': ratio,
                    'warning': 'May be ignoring negative feedback'
                }
        
        return None


class InefficiencyDetector:
    """Detect inefficiencies in learning process."""
    
    @staticmethod
    def detect_slow_strategies(strategy_performance: Dict[str, StrategyOutcome]) -> List[Dict[str, Any]]:
        """Detect strategies that are slower than average."""
        if not strategy_performance:
            return []
        
        avg_duration = sum(s.avg_duration_ms for s in strategy_performance.values()) / len(strategy_performance)
        slow_strategies = []
        
        for name, outcome in strategy_performance.items():
            if outcome.avg_duration_ms > avg_duration * 2:  # 2x slower than average
                slow_strategies.append({
                    'type': 'slow_strategy',
                    'strategy': name,
                    'avg_duration_ms': outcome.avg_duration_ms,
                    'avg_all': avg_duration,
                    'slowdown_factor': outcome.avg_duration_ms / avg_duration
                })
        
        return slow_strategies
    
    @staticmethod
    def detect_redundant_processing(events: List[LearningEvent]) -> List[Dict[str, Any]]:
        """Detect redundant processing of similar inputs."""
        redundant = []
        seen_inputs = {}
        
        for event in events:
            input_key = json.dumps(event.input_data, sort_keys=True)
            
            if input_key in seen_inputs:
                seen_inputs[input_key].append(event)
            else:
                seen_inputs[input_key] = [event]
        
        for input_key, event_list in seen_inputs.items():
            if len(event_list) > 3:  # Same input processed >3 times
                redundant.append({
                    'type': 'redundant_processing',
                    'input': json.loads(input_key),
                    'occurrences': len(event_list),
                    'recommendation': 'Cache results for this input pattern'
                })
        
        return redundant


class MetaOptimizer:
    """Main meta-optimizer orchestrator."""
    
    def __init__(self, journal: LearningJournal):
        self.journal = journal
        self.stagnation_detector = StagnationDetector()
        self.bias_detector = BiasDetector()
        self.inefficiency_detector = InefficiencyDetector()
    
    def analyze_learning_health(self) -> Dict[str, Any]:
        """Comprehensive health check of learning system."""
        summary = self.journal.get_learning_summary(days=7)
        strategy_performance = self.journal.get_strategy_performance()
        recent_events = self.journal.get_recent_events(limit=100)
        patterns = self.journal.detect_patterns()
        
        health_report = {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_health': 'healthy',  # Will update based on findings
            'summary': summary,
            'issues': [],
            'recommendations': []
        }
        
        # Check for stagnation
        confidence_timeline = self.journal.get_growth_timeline('avg_confidence', days=30)
        plateau = self.stagnation_detector.detect_plateau(confidence_timeline)
        
        if plateau:
            health_report['issues'].append({
                'type': 'stagnation',
                'severity': 'medium',
                'details': plateau
            })
            health_report['overall_health'] = 'degraded'
        
        # Check for biases
        overreliance = self.bias_detector.detect_overreliance(strategy_performance)
        underperforming = self.bias_detector.detect_underperforming(strategy_performance)
        
        health_report['issues'].extend(overreliance)
        health_report['issues'].extend(underperforming)
        
        if overreliance or underperforming:
            health_report['overall_health'] = 'needs_attention'
        
        # Check for inefficiencies
        slow_strategies = self.inefficiency_detector.detect_slow_strategies(strategy_performance)
        redundant = self.inefficiency_detector.detect_redundant_processing(recent_events)
        
        health_report['issues'].extend(slow_strategies)
        health_report['issues'].extend(redundant)
        
        # Patterns from journal
        health_report['patterns'] = patterns
        
        return health_report
    
    def propose_optimizations(self) -> List[OptimizationProposal]:
        """Generate optimization proposals."""
        proposals = []
        health = self.analyze_learning_health()
        strategy_performance = self.journal.get_strategy_performance()
        
        # Proposal: Adjust recall threshold if confidence declining
        confidence_timeline = self.journal.get_growth_timeline('avg_confidence', days=30)
        decline = self.stagnation_detector.detect_decline(confidence_timeline)
        
        if decline:
            proposals.append(OptimizationProposal(
                proposal_id=f"prop_{datetime.utcnow().timestamp()}_1",
                category='parameter',
                target='recall_threshold',
                current_value=0.5,
                proposed_value=0.4,
                rationale=f"Confidence declined by {decline['decline_percentage']:.1%}, lowering threshold may help",
                expected_improvement=0.15,
                confidence=0.7,
                priority='high'
            ))
        
        # Proposal: Retire underperforming strategies
        for issue in health['issues']:
            if issue.get('type') == 'underperforming':
                proposals.append(OptimizationProposal(
                    proposal_id=f"prop_{datetime.utcnow().timestamp()}_2",
                    category='strategy',
                    target=issue['strategy'],
                    current_value='active',
                    proposed_value='retired',
                    rationale=f"Success rate {issue['success_rate']:.1%} after {issue['total_uses']} uses",
                    expected_improvement=0.1,
                    confidence=0.8,
                    priority='medium'
                ))
        
        # Proposal: Increase exploration if overreliant
        for issue in health['issues']:
            if issue.get('type') == 'overreliance':
                proposals.append(OptimizationProposal(
                    proposal_id=f"prop_{datetime.utcnow().timestamp()}_3",
                    category='parameter',
                    target='exploration_rate',
                    current_value=0.1,
                    proposed_value=0.25,
                    rationale=f"Over-relying on {issue['strategy']} ({issue['usage_percentage']:.1%} of uses)",
                    expected_improvement=0.2,
                    confidence=0.75,
                    priority='high'
                ))
        
        # Proposal: Add caching for redundant processing
        redundant_issues = [i for i in health['issues'] if i.get('type') == 'redundant_processing']
        if redundant_issues:
            proposals.append(OptimizationProposal(
                proposal_id=f"prop_{datetime.utcnow().timestamp()}_4",
                category='architecture',
                target='result_caching',
                current_value=False,
                proposed_value=True,
                rationale=f"Detected {len(redundant_issues)} redundant processing patterns",
                expected_improvement=0.3,
                confidence=0.9,
                priority='medium'
            ))
        
        # Sort by priority and expected improvement
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        proposals.sort(key=lambda p: (priority_order[p.priority], -p.expected_improvement))
        
        return proposals
    
    def reflect_on_failure(self, failed_event: LearningEvent) -> Dict[str, Any]:
        """Reflect on a specific failure and generate insights."""
        reflection = {
            'event_id': failed_event.event_id,
            'timestamp': datetime.utcnow().isoformat(),
            'failure_analysis': {},
            'insights': [],
            'proposed_changes': []
        }
        
        # Analyze failure context
        method = failed_event.method_used
        strategy_perf = self.journal.get_strategy_performance(method)
        
        if method in strategy_perf:
            outcome = strategy_perf[method]
            reflection['failure_analysis'] = {
                'method': method,
                'historical_success_rate': outcome.success_rate(),
                'total_uses': outcome.total_uses,
                'avg_confidence': outcome.avg_confidence
            }
            
            # Generate insights
            if outcome.success_rate() < 0.5:
                reflection['insights'].append(
                    f"Method '{method}' has low success rate ({outcome.success_rate():.1%})"
                )
                reflection['proposed_changes'].append(
                    f"Consider alternative methods or refine '{method}' implementation"
                )
            
            if failed_event.confidence < 0.3:
                reflection['insights'].append(
                    f"Very low confidence ({failed_event.confidence:.1%}) indicates uncertainty"
                )
                reflection['proposed_changes'].append(
                    "Add more training data or clarification mechanism for low-confidence scenarios"
                )
        
        # Check for similar past failures
        recent_failures = self.journal.get_recent_events(limit=50, event_type='failure')
        similar_failures = [
            e for e in recent_failures 
            if e.method_used == method and e.event_id != failed_event.event_id
        ]
        
        if len(similar_failures) >= 3:
            reflection['insights'].append(
                f"Repeated failures with '{method}' detected ({len(similar_failures)} in recent history)"
            )
            reflection['proposed_changes'].append(
                f"Urgent: Review and fix '{method}' or disable temporarily"
            )
        
        # Store reflection
        self.journal.add_reflection(
            trigger=f"failure_{failed_event.event_id}",
            analysis=json.dumps(reflection['failure_analysis']),
            insights=reflection['insights'],
            proposed_changes=reflection['proposed_changes']
        )
        
        return reflection
    
    def audit_learning(self, days: int = 30) -> Dict[str, Any]:
        """Comprehensive learning audit."""
        audit = {
            'audit_timestamp': datetime.utcnow().isoformat(),
            'period_days': days,
            'summary': self.journal.get_learning_summary(days=days),
            'strategy_performance': {},
            'growth_metrics': {},
            'health_check': self.analyze_learning_health(),
            'optimization_proposals': [p.__dict__ for p in self.propose_optimizations()],
            'reflections': self.journal.get_reflections(limit=10)
        }
        
        # Strategy performance
        perf = self.journal.get_strategy_performance()
        audit['strategy_performance'] = {
            name: {
                'success_rate': outcome.success_rate(),
                'total_uses': outcome.total_uses,
                'avg_confidence': outcome.avg_confidence,
                'avg_duration_ms': outcome.avg_duration_ms
            }
            for name, outcome in perf.items()
        }
        
        # Growth metrics
        metrics = ['avg_confidence', 'success_rate', 'learning_velocity']
        for metric in metrics:
            timeline = self.journal.get_growth_timeline(metric, days=days)
            if timeline:
                values = [v for _, v in timeline]
                audit['growth_metrics'][metric] = {
                    'current': values[-1] if values else 0,
                    'avg': sum(values) / len(values) if values else 0,
                    'trend': 'improving' if len(values) > 1 and values[-1] > values[0] else 'declining'
                }
        
        return audit
    
    def auto_optimize(self, apply_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Automatically apply high-confidence optimizations."""
        proposals = self.propose_optimizations()
        applied = []
        
        for proposal in proposals:
            if proposal.confidence >= apply_threshold and proposal.priority in ['critical', 'high']:
                # In production, this would actually apply the change
                # For now, just log it
                applied.append({
                    'proposal_id': proposal.proposal_id,
                    'target': proposal.target,
                    'old_value': proposal.current_value,
                    'new_value': proposal.proposed_value,
                    'rationale': proposal.rationale,
                    'applied_at': datetime.utcnow().isoformat()
                })
                
                # Log as learning event
                self.journal.log_event(LearningEvent(
                    event_id=f"auto_opt_{proposal.proposal_id}",
                    timestamp=datetime.utcnow(),
                    event_type='optimization',
                    input_data={'proposal': proposal.__dict__},
                    method_used='auto_optimize',
                    result={'applied': True},
                    confidence=proposal.confidence,
                    success=True,
                    context={'category': proposal.category}
                ))
        
        return applied
