#!/usr/bin/env python3
"""
Monte Carlo Planner: Advanced probabilistic simulation with outcome visualization.
Features: Multi-path analysis, risk/reward scoring, rollback planning, outcome ranking.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import json
import random
import statistics


@dataclass
class SimulationOutcome:
    """Result of a single simulation run."""
    outcome_id: str
    success: bool
    probability: float
    risk_score: float
    reward_score: float
    confidence: float
    path: List[str]
    final_state: Dict[str, Any]
    rollback_plan: List[str]
    impact_metrics: Dict[str, float]


@dataclass
class PathAnalysis:
    """Analysis of a specific path through decision space."""
    path_id: str
    description: str
    success_rate: float
    avg_risk: float
    avg_reward: float
    confidence: float
    recommended: bool
    sample_outcomes: List[SimulationOutcome]
    visualization: str


class OutcomeVisualizer:
    """Generate visualizations of simulation outcomes."""
    
    @staticmethod
    def create_risk_reward_chart(outcomes: List[SimulationOutcome]) -> str:
        """Create ASCII chart of risk vs reward."""
        if not outcomes:
            return "No outcomes to visualize"
        
        # Build chart
        chart = ["Risk/Reward Analysis:", ""]
        chart.append("Risk  →")
        chart.append("Low   Med   High")
        chart.append("│     │     │")
        
        # Categorize outcomes
        low_risk = [o for o in outcomes if o.risk_score < 0.33]
        med_risk = [o for o in outcomes if 0.33 <= o.risk_score < 0.66]
        high_risk = [o for o in outcomes if o.risk_score >= 0.66]
        
        high_reward = len([o for o in outcomes if o.reward_score > 0.66])
        med_reward = len([o for o in outcomes if 0.33 <= o.reward_score <= 0.66])
        low_reward = len([o for o in outcomes if o.reward_score < 0.33])
        
        chart.append(f"High Reward: {len([o for o in low_risk if o.reward_score > 0.66]):3} | "
                    f"{len([o for o in med_risk if o.reward_score > 0.66]):3} | "
                    f"{len([o for o in high_risk if o.reward_score > 0.66]):3}")
        
        chart.append(f"Med  Reward: {len([o for o in low_risk if 0.33 <= o.reward_score <= 0.66]):3} | "
                    f"{len([o for o in med_risk if 0.33 <= o.reward_score <= 0.66]):3} | "
                    f"{len([o for o in high_risk if 0.33 <= o.reward_score <= 0.66]):3}")
        
        chart.append(f"Low  Reward: {len([o for o in low_risk if o.reward_score < 0.33]):3} | "
                    f"{len([o for o in med_risk if o.reward_score < 0.33]):3} | "
                    f"{len([o for o in high_risk if o.reward_score < 0.33]):3}")
        
        return "\n".join(chart)
    
    @staticmethod
    def create_timeline_viz(path: List[str]) -> str:
        """Create timeline visualization of a path."""
        if not path:
            return "No path to visualize"
        
        viz = ["Timeline:", ""]
        for i, step in enumerate(path):
            prefix = "START" if i == 0 else f"T+{i}"
            arrow = " → " if i < len(path) - 1 else ""
            viz.append(f"{prefix:6} {step}{arrow}")
        
        return "\n".join(viz)


class PathOptimizer:
    """Optimize paths through decision space."""
    
    @staticmethod
    def find_pareto_optimal(outcomes: List[SimulationOutcome]) -> List[SimulationOutcome]:
        """Find Pareto-optimal outcomes (not dominated on any dimension)."""
        pareto = []
        
        for candidate in outcomes:
            dominated = False
            
            for other in outcomes:
                if other.outcome_id == candidate.outcome_id:
                    continue
                
                # Check if other dominates candidate
                if (other.reward_score >= candidate.reward_score and
                    other.risk_score <= candidate.risk_score and
                    other.confidence >= candidate.confidence and
                    (other.reward_score > candidate.reward_score or
                     other.risk_score < candidate.risk_score or
                     other.confidence > candidate.confidence)):
                    dominated = True
                    break
            
            if not dominated:
                pareto.append(candidate)
        
        return pareto
    
    @staticmethod
    def calculate_utility(outcome: SimulationOutcome, 
                         risk_aversion: float = 0.5) -> float:
        """Calculate utility score with risk aversion parameter."""
        # Utility = Reward * Confidence - Risk * risk_aversion
        utility = (outcome.reward_score * outcome.confidence - 
                  outcome.risk_score * risk_aversion)
        return utility


class MonteCarloPlanner:
    """Advanced Monte Carlo simulation planner."""
    
    def __init__(self, conn):
        self.conn = conn
        self.visualizer = OutcomeVisualizer()
        self.optimizer = PathOptimizer()
        self._init_db()
    
    def _init_db(self):
        """Initialize database tables."""
        cur = self.conn.cursor()
        
        cur.execute('''
            CREATE TABLE IF NOT EXISTS simulation_runs (
                run_id TEXT PRIMARY KEY,
                goal TEXT NOT NULL,
                num_iterations INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                results TEXT NOT NULL
            )
        ''')
        
        self.conn.commit()
    
    def simulate_goal(self, goal: str, 
                     initial_state: Dict[str, Any],
                     num_iterations: int = 1000,
                     risk_aversion: float = 0.5) -> Dict[str, Any]:
        """Run Monte Carlo simulation for a goal."""
        run_id = f"run_{datetime.utcnow().timestamp()}"
        outcomes = []
        
        for i in range(num_iterations):
            outcome = self._simulate_single_run(goal, initial_state, i)
            outcomes.append(outcome)
        
        # Analyze outcomes
        analysis = self._analyze_outcomes(outcomes, risk_aversion)
        
        # Store results
        self._store_simulation(run_id, goal, num_iterations, analysis)
        
        return {
            'run_id': run_id,
            'goal': goal,
            'iterations': num_iterations,
            'analysis': analysis
        }
    
    def _simulate_single_run(self, goal: str, 
                            initial_state: Dict[str, Any],
                            iteration: int) -> SimulationOutcome:
        """Run single simulation iteration."""
        # Simulate path through decision space
        path = []
        current_state = initial_state.copy()
        
        # Simple simulation: make random decisions
        num_steps = random.randint(3, 7)
        for step in range(num_steps):
            action = self._choose_action(goal, current_state, step)
            path.append(action)
            current_state = self._apply_action(current_state, action)
        
        # Evaluate outcome
        success = self._evaluate_success(goal, current_state)
        
        # Calculate scores
        risk = self._calculate_risk(path, current_state)
        reward = self._calculate_reward(goal, current_state, success)
        confidence = self._calculate_confidence(path)
        probability = self._calculate_probability(success, risk, reward)
        
        # Generate rollback plan
        rollback = self._generate_rollback(path)
        
        # Calculate impact
        impact = self._calculate_impact(initial_state, current_state)
        
        return SimulationOutcome(
            outcome_id=f"outcome_{iteration}",
            success=success,
            probability=probability,
            risk_score=risk,
            reward_score=reward,
            confidence=confidence,
            path=path,
            final_state=current_state,
            rollback_plan=rollback,
            impact_metrics=impact
        )
    
    def _choose_action(self, goal: str, state: Dict[str, Any], step: int) -> str:
        """Choose action based on goal and current state."""
        # Simplified action selection
        if 'bedtime' in goal.lower():
            actions = [
                'Enable bedtime policy',
                'Send notification to devices',
                'Gradually reduce screen brightness',
                'Block non-essential apps',
                'Enable sleep mode'
            ]
        elif 'device' in goal.lower():
            actions = [
                'Check device status',
                'Restart device',
                'Switch to backup device',
                'Run diagnostics',
                'Update configuration'
            ]
        else:
            actions = [
                'Analyze situation',
                'Execute planned action',
                'Monitor results',
                'Adjust parameters',
                'Verify success'
            ]
        
        return random.choice(actions)
    
    def _apply_action(self, state: Dict[str, Any], action: str) -> Dict[str, Any]:
        """Apply action to state."""
        new_state = state.copy()
        
        # Simulate state changes
        if 'enable' in action.lower() or 'activate' in action.lower():
            new_state['active_policies'] = new_state.get('active_policies', 0) + 1
        
        if 'notification' in action.lower():
            new_state['notifications_sent'] = new_state.get('notifications_sent', 0) + 1
        
        if 'block' in action.lower():
            new_state['restrictions'] = new_state.get('restrictions', 0) + 1
        
        # Random state changes
        new_state['compliance'] = max(0, min(1, 
            new_state.get('compliance', 0.7) + random.uniform(-0.1, 0.15)))
        
        return new_state
    
    def _evaluate_success(self, goal: str, final_state: Dict[str, Any]) -> bool:
        """Evaluate if goal was achieved."""
        # Success criteria
        compliance = final_state.get('compliance', 0)
        active_policies = final_state.get('active_policies', 0)
        
        return compliance > 0.6 and active_policies > 0
    
    def _calculate_risk(self, path: List[str], state: Dict[str, Any]) -> float:
        """Calculate risk score."""
        risk = 0.0
        
        # More steps = more risk
        risk += len(path) * 0.05
        
        # High restrictions = higher risk
        restrictions = state.get('restrictions', 0)
        risk += restrictions * 0.1
        
        # Random variation
        risk += random.uniform(0, 0.2)
        
        return min(1.0, risk)
    
    def _calculate_reward(self, goal: str, state: Dict[str, Any], success: bool) -> float:
        """Calculate reward score."""
        reward = 0.5 if success else 0.2
        
        # High compliance = higher reward
        compliance = state.get('compliance', 0.5)
        reward += compliance * 0.3
        
        # Policies active = good
        reward += min(0.2, state.get('active_policies', 0) * 0.1)
        
        return min(1.0, reward)
    
    def _calculate_confidence(self, path: List[str]) -> float:
        """Calculate confidence in prediction."""
        # Shorter paths = higher confidence
        confidence = 1.0 - (len(path) * 0.05)
        
        # Add random variation
        confidence += random.uniform(-0.1, 0.1)
        
        return max(0.3, min(1.0, confidence))
    
    def _calculate_probability(self, success: bool, risk: float, reward: float) -> float:
        """Calculate outcome probability."""
        base_prob = 0.7 if success else 0.3
        
        # Adjust for risk and reward
        prob = base_prob * (1.0 - risk * 0.3) * (0.7 + reward * 0.3)
        
        return max(0.05, min(0.95, prob))
    
    def _generate_rollback(self, path: List[str]) -> List[str]:
        """Generate rollback plan."""
        rollback = []
        
        for action in reversed(path):
            # Generate inverse actions
            if 'enable' in action.lower():
                rollback.append(action.replace('Enable', 'Disable'))
            elif 'send' in action.lower():
                rollback.append('Clear notifications')
            elif 'block' in action.lower():
                rollback.append(action.replace('Block', 'Unblock'))
            else:
                rollback.append(f"Undo: {action}")
        
        rollback.append("Verify system restored to initial state")
        
        return rollback
    
    def _calculate_impact(self, initial: Dict[str, Any], 
                         final: Dict[str, Any]) -> Dict[str, float]:
        """Calculate impact metrics."""
        impact = {}
        
        # Compliance change
        impact['compliance_delta'] = (final.get('compliance', 0) - 
                                     initial.get('compliance', 0))
        
        # Policy changes
        impact['policy_delta'] = (final.get('active_policies', 0) - 
                                 initial.get('active_policies', 0))
        
        # Restrictions
        impact['restrictions_added'] = final.get('restrictions', 0)
        
        return impact
    
    def _analyze_outcomes(self, outcomes: List[SimulationOutcome],
                         risk_aversion: float) -> Dict[str, Any]:
        """Analyze simulation outcomes."""
        # Calculate statistics
        success_rate = sum(1 for o in outcomes if o.success) / len(outcomes)
        avg_risk = statistics.mean(o.risk_score for o in outcomes)
        avg_reward = statistics.mean(o.reward_score for o in outcomes)
        avg_confidence = statistics.mean(o.confidence for o in outcomes)
        
        # Find Pareto optimal outcomes
        pareto = self.optimizer.find_pareto_optimal(outcomes)
        
        # Rank by utility
        ranked = sorted(outcomes, 
                       key=lambda o: self.optimizer.calculate_utility(o, risk_aversion),
                       reverse=True)
        
        # Generate top 3 paths
        top_paths = self._generate_path_analysis(ranked[:3])
        
        # Create visualization
        viz = self.visualizer.create_risk_reward_chart(outcomes)
        
        return {
            'summary': {
                'success_rate': success_rate,
                'avg_risk': avg_risk,
                'avg_reward': avg_reward,
                'avg_confidence': avg_confidence,
                'pareto_optimal_count': len(pareto)
            },
            'top_paths': top_paths,
            'visualization': viz
        }
    
    def _generate_path_analysis(self, outcomes: List[SimulationOutcome]) -> List[PathAnalysis]:
        """Generate detailed analysis for top paths."""
        analyses = []
        
        for i, outcome in enumerate(outcomes):
            analysis = PathAnalysis(
                path_id=f"path_{i+1}",
                description=f"Path {i+1}: {len(outcome.path)} steps",
                success_rate=1.0 if outcome.success else 0.0,
                avg_risk=outcome.risk_score,
                avg_reward=outcome.reward_score,
                confidence=outcome.confidence,
                recommended=(i == 0),
                sample_outcomes=[outcome],
                visualization=self.visualizer.create_timeline_viz(outcome.path)
            )
            analyses.append(analysis)
        
        return analyses
    
    def _store_simulation(self, run_id: str, goal: str, 
                         iterations: int, results: Dict[str, Any]):
        """Store simulation results."""
        cur = self.conn.cursor()
        cur.execute('''
            INSERT INTO simulation_runs (run_id, goal, num_iterations, timestamp, results)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            run_id,
            goal,
            iterations,
            datetime.utcnow().isoformat(),
            json.dumps(results)
        ))
        self.conn.commit()
    
    def get_simulation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent simulation runs."""
        cur = self.conn.cursor()
        cur.execute('''
            SELECT run_id, goal, num_iterations, timestamp
            FROM simulation_runs
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        return [
            {
                'run_id': row[0],
                'goal': row[1],
                'iterations': row[2],
                'timestamp': row[3]
            }
            for row in cur.fetchall()
        ]
