#!/usr/bin/env python3
"""
Explainability Engine: Generate natural language explanations for AI decisions.
Features: Reasoning chains, decision graphs, confidence attribution, counterfactual explanations.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
import json


@dataclass
class ReasoningStep:
    """Single step in reasoning chain."""
    step_id: str
    description: str
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    confidence: float
    method: str  # rule, inference, calculation, etc.
    dependencies: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class DecisionNode:
    """Node in decision graph."""
    node_id: str
    decision: str
    factors: List[Dict[str, Any]]
    weight: float
    confidence: float
    children: List[str] = field(default_factory=list)


class ReasoningChain:
    """Traceable chain of reasoning steps."""
    
    def __init__(self, query: str):
        self.query = query
        self.steps: List[ReasoningStep] = []
        self.final_answer: Optional[Any] = None
        self.overall_confidence: float = 1.0
    
    def add_step(self, step: ReasoningStep):
        """Add reasoning step and update confidence."""
        self.steps.append(step)
        # Confidence propagates multiplicatively
        self.overall_confidence *= step.confidence
    
    def to_narrative(self) -> str:
        """Generate natural language narrative."""
        if not self.steps:
            return "No reasoning steps recorded."
        
        narrative = f"To answer '{self.query}', I went through the following reasoning:\n\n"
        
        for i, step in enumerate(self.steps, 1):
            narrative += f"{i}. {step.description}\n"
            
            if step.dependencies:
                narrative += f"   (Based on steps: {', '.join(str(self.steps.index(s)+1) for s in self.steps if s.step_id in step.dependencies)})\n"
            
            narrative += f"   Confidence: {step.confidence:.2%}\n\n"
        
        narrative += f"Final confidence: {self.overall_confidence:.2%}\n"
        return narrative
    
    def get_critical_path(self) -> List[ReasoningStep]:
        """Get most impactful steps (lowest confidence)."""
        sorted_steps = sorted(self.steps, key=lambda s: s.confidence)
        return sorted_steps[:3]


class DecisionGraph:
    """Hierarchical graph of decision factors."""
    
    def __init__(self, root_decision: str):
        self.root_decision = root_decision
        self.nodes: Dict[str, DecisionNode] = {}
        self.root_id: Optional[str] = None
    
    def add_node(self, node: DecisionNode, parent_id: Optional[str] = None):
        """Add node to graph."""
        self.nodes[node.node_id] = node
        
        if parent_id is None:
            self.root_id = node.node_id
        else:
            if parent_id in self.nodes:
                self.nodes[parent_id].children.append(node.node_id)
    
    def explain_decision(self, node_id: Optional[str] = None) -> str:
        """Generate explanation for decision."""
        if node_id is None:
            node_id = self.root_id
        
        if node_id not in self.nodes:
            return "Decision not found."
        
        node = self.nodes[node_id]
        explanation = f"Decision: {node.decision}\n"
        explanation += f"Confidence: {node.confidence:.2%}\n\n"
        explanation += "Key factors:\n"
        
        for i, factor in enumerate(node.factors, 1):
            explanation += f"  {i}. {factor.get('name', 'Unknown')}: "
            explanation += f"{factor.get('value', 'N/A')} "
            explanation += f"(importance: {factor.get('importance', 0):.2f})\n"
        
        if node.children:
            explanation += f"\nThis decision led to {len(node.children)} subsequent decisions.\n"
        
        return explanation
    
    def get_attribution(self) -> Dict[str, float]:
        """Calculate feature attribution scores."""
        attribution = {}
        
        for node in self.nodes.values():
            for factor in node.factors:
                name = factor.get('name', 'unknown')
                importance = factor.get('importance', 0.0) * node.weight
                attribution[name] = attribution.get(name, 0.0) + importance
        
        # Normalize
        total = sum(attribution.values())
        if total > 0:
            attribution = {k: v/total for k, v in attribution.items()}
        
        return attribution


class ConfidenceTracker:
    """Track confidence across components."""
    
    def __init__(self):
        self.components: Dict[str, List[float]] = {}
    
    def record(self, component: str, confidence: float):
        """Record confidence score."""
        if component not in self.components:
            self.components[component] = []
        self.components[component].append(confidence)
    
    def get_breakdown(self) -> Dict[str, Dict[str, float]]:
        """Get confidence breakdown by component."""
        breakdown = {}
        
        for component, scores in self.components.items():
            breakdown[component] = {
                'mean': sum(scores) / len(scores),
                'min': min(scores),
                'max': max(scores),
                'count': len(scores)
            }
        
        return breakdown
    
    def identify_weak_links(self, threshold: float = 0.6) -> List[str]:
        """Identify low-confidence components."""
        weak = []
        
        for component, scores in self.components.items():
            avg = sum(scores) / len(scores)
            if avg < threshold:
                weak.append(component)
        
        return weak


class CounterfactualExplainer:
    """Generate counterfactual explanations."""
    
    @staticmethod
    def generate_counterfactual(original_input: Dict[str, Any], 
                               desired_output: Any,
                               feature_ranges: Dict[str, Tuple[Any, Any]]) -> Dict[str, Any]:
        """Generate minimal changes to achieve desired output."""
        # Simplified: suggest changing one feature at a time
        suggestions = []
        
        for feature, (min_val, max_val) in feature_ranges.items():
            current = original_input.get(feature)
            
            if current is not None:
                # Suggest moving toward range extremes
                suggestions.append({
                    'feature': feature,
                    'current_value': current,
                    'suggested_value': max_val if current < (min_val + max_val) / 2 else min_val,
                    'explanation': f"Change {feature} to {max_val if current < (min_val + max_val) / 2 else min_val}"
                })
        
        return {
            'original_input': original_input,
            'desired_output': desired_output,
            'suggestions': suggestions[:3],  # Top 3
            'explanation': f"To achieve {desired_output}, consider these changes."
        }


class ExplainabilityEngine:
    """Main explainability orchestrator."""
    
    def __init__(self, conn):
        self.conn = conn
        self.confidence_tracker = ConfidenceTracker()
        self.reasoning_chains: Dict[str, ReasoningChain] = {}
        self.decision_graphs: Dict[str, DecisionGraph] = {}
        self._init_db()
    
    def _init_db(self):
        cur = self.conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS explanations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                explanation_type TEXT NOT NULL,
                content TEXT NOT NULL,
                confidence REAL,
                timestamp TEXT NOT NULL
            )
        ''')
        self.conn.commit()
    
    def create_reasoning_chain(self, query: str) -> str:
        """Start new reasoning chain."""
        chain_id = f"chain_{datetime.utcnow().timestamp()}"
        self.reasoning_chains[chain_id] = ReasoningChain(query)
        return chain_id
    
    def add_reasoning_step(self, chain_id: str, step: ReasoningStep):
        """Add step to reasoning chain."""
        if chain_id in self.reasoning_chains:
            self.reasoning_chains[chain_id].add_step(step)
            self.confidence_tracker.record(step.method, step.confidence)
    
    def explain_reasoning(self, chain_id: str) -> str:
        """Generate explanation for reasoning chain."""
        if chain_id not in self.reasoning_chains:
            return "Reasoning chain not found."
        
        chain = self.reasoning_chains[chain_id]
        narrative = chain.to_narrative()
        
        # Store explanation
        self._store_explanation(chain.query, 'reasoning_chain', narrative, chain.overall_confidence)
        
        return narrative
    
    def create_decision_graph(self, decision: str) -> str:
        """Create new decision graph."""
        graph_id = f"graph_{datetime.utcnow().timestamp()}"
        self.decision_graphs[graph_id] = DecisionGraph(decision)
        return graph_id
    
    def add_decision_node(self, graph_id: str, node: DecisionNode, parent_id: Optional[str] = None):
        """Add node to decision graph."""
        if graph_id in self.decision_graphs:
            self.decision_graphs[graph_id].add_node(node, parent_id)
            self.confidence_tracker.record('decision', node.confidence)
    
    def explain_decision(self, graph_id: str, node_id: Optional[str] = None) -> str:
        """Generate explanation for decision."""
        if graph_id not in self.decision_graphs:
            return "Decision graph not found."
        
        graph = self.decision_graphs[graph_id]
        explanation = graph.explain_decision(node_id)
        
        # Store explanation
        self._store_explanation(graph.root_decision, 'decision_graph', explanation, 
                               graph.nodes.get(node_id or graph.root_id, DecisionNode('', '', [], 0, 0)).confidence)
        
        return explanation
    
    def get_attribution(self, graph_id: str) -> Dict[str, float]:
        """Get feature attribution."""
        if graph_id not in self.decision_graphs:
            return {}
        
        return self.decision_graphs[graph_id].get_attribution()
    
    def explain_with_counterfactual(self, original_input: Dict[str, Any],
                                   current_output: Any,
                                   desired_output: Any,
                                   feature_ranges: Dict[str, Tuple[Any, Any]]) -> Dict[str, Any]:
        """Generate counterfactual explanation."""
        result = CounterfactualExplainer.generate_counterfactual(
            original_input, desired_output, feature_ranges
        )
        
        # Store explanation
        explanation_text = json.dumps(result, indent=2)
        self._store_explanation(
            f"Counterfactual: {current_output} -> {desired_output}",
            'counterfactual',
            explanation_text,
            0.8
        )
        
        return result
    
    def get_confidence_report(self) -> Dict[str, Any]:
        """Generate comprehensive confidence report."""
        breakdown = self.confidence_tracker.get_breakdown()
        weak_links = self.confidence_tracker.identify_weak_links()
        
        return {
            'confidence_breakdown': breakdown,
            'weak_components': weak_links,
            'overall_stats': {
                'total_components': len(breakdown),
                'healthy_components': len(breakdown) - len(weak_links),
                'needs_attention': len(weak_links)
            }
        }
    
    def generate_summary(self, query: str, answer: Any, confidence: float,
                        key_factors: List[str]) -> str:
        """Generate human-readable summary."""
        summary = f"Query: {query}\n"
        summary += f"Answer: {answer}\n"
        summary += f"Confidence: {confidence:.2%}\n\n"
        
        if confidence > 0.8:
            summary += "I am highly confident in this answer because:\n"
        elif confidence > 0.6:
            summary += "I am moderately confident in this answer, considering:\n"
        else:
            summary += "I have low confidence in this answer due to:\n"
        
        for i, factor in enumerate(key_factors, 1):
            summary += f"  {i}. {factor}\n"
        
        if confidence < 0.7:
            summary += "\nPlease verify this answer independently."
        
        return summary
    
    def _store_explanation(self, query: str, exp_type: str, content: str, confidence: float):
        """Store explanation in database."""
        cur = self.conn.cursor()
        cur.execute('''
            INSERT INTO explanations (query, explanation_type, content, confidence, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (query, exp_type, content, confidence, datetime.utcnow().isoformat()))
        self.conn.commit()
    
    def get_explanation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent explanations."""
        cur = self.conn.cursor()
        cur.execute('''
            SELECT query, explanation_type, content, confidence, timestamp
            FROM explanations
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        results = []
        for row in cur.fetchall():
            results.append({
                'query': row[0],
                'type': row[1],
                'content': row[2],
                'confidence': row[3],
                'timestamp': row[4]
            })
        
        return results
