#!/usr/bin/env python3
"""
Temporal Reasoning Engine: Time-aware inference, causality, counterfactuals, timeline simulation.
Features: Event ordering, causal graphs, temporal constraints, what-if analysis, Allen's interval algebra.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
from collections import defaultdict, deque


class TemporalRelation(Enum):
    """Allen's interval algebra relations."""
    BEFORE = "before"
    AFTER = "after"
    MEETS = "meets"
    MET_BY = "met_by"
    OVERLAPS = "overlaps"
    OVERLAPPED_BY = "overlapped_by"
    STARTS = "starts"
    STARTED_BY = "started_by"
    DURING = "during"
    CONTAINS = "contains"
    FINISHES = "finishes"
    FINISHED_BY = "finished_by"
    EQUALS = "equals"


@dataclass
class TemporalEvent:
    """Event with temporal bounds and metadata."""
    event_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    event_type: str = "generic"
    attributes: Dict[str, Any] = field(default_factory=dict)
    caused_by: List[str] = field(default_factory=list)  # Causal predecessors
    effects: List[str] = field(default_factory=list)  # Causal successors
    confidence: float = 1.0
    
    def duration(self) -> Optional[timedelta]:
        """Get event duration."""
        if self.end_time:
            return self.end_time - self.start_time
        return None
    
    def is_instantaneous(self) -> bool:
        """Check if event is a point in time."""
        return self.end_time is None or self.end_time == self.start_time


@dataclass
class CausalLink:
    """Causal relationship between events."""
    cause: str  # event_id
    effect: str  # event_id
    strength: float = 1.0  # 0-1
    delay: Optional[timedelta] = None
    mechanism: Optional[str] = None


class TemporalConstraintNetwork:
    """Simple Temporal Network for constraint reasoning."""
    
    def __init__(self):
        self.constraints: Dict[Tuple[str, str], Tuple[float, float]] = {}  # (from, to) -> (min_delta, max_delta)
        self.events: Set[str] = set()
    
    def add_constraint(self, from_event: str, to_event: str, min_delta: float, max_delta: float):
        """Add temporal constraint: to_event occurs [min_delta, max_delta] after from_event."""
        self.events.add(from_event)
        self.events.add(to_event)
        self.constraints[(from_event, to_event)] = (min_delta, max_delta)
    
    def is_consistent(self) -> bool:
        """Check if network is temporally consistent using Floyd-Warshall."""
        # Build distance matrix
        events_list = list(self.events)
        n = len(events_list)
        event_to_idx = {e: i for i, e in enumerate(events_list)}
        
        # Initialize with inf
        dist_min = [[float('inf')] * n for _ in range(n)]
        dist_max = [[float('-inf')] * n for _ in range(n)]
        
        for i in range(n):
            dist_min[i][i] = 0
            dist_max[i][i] = 0
        
        # Add constraints
        for (from_e, to_e), (min_d, max_d) in self.constraints.items():
            i, j = event_to_idx[from_e], event_to_idx[to_e]
            dist_min[i][j] = min(dist_min[i][j], min_d)
            dist_max[i][j] = max(dist_max[i][j], max_d)
        
        # Floyd-Warshall for all-pairs shortest/longest paths
        for k in range(n):
            for i in range(n):
                for j in range(n):
                    dist_min[i][j] = min(dist_min[i][j], dist_min[i][k] + dist_min[k][j])
                    dist_max[i][j] = max(dist_max[i][j], dist_max[i][k] + dist_max[k][j])
        
        # Check for negative cycles or inconsistencies
        for i in range(n):
            if dist_min[i][i] < 0 or dist_max[i][i] > 0:
                return False
            for j in range(n):
                if dist_min[i][j] > dist_max[i][j]:
                    return False
        
        return True
    
    def get_possible_orderings(self) -> List[List[str]]:
        """Get all consistent total orderings (simplified)."""
        if not self.is_consistent():
            return []
        
        # Topological sort considering constraints
        in_degree = defaultdict(int)
        graph = defaultdict(list)
        
        for (from_e, to_e), (min_d, max_d) in self.constraints.items():
            if min_d > 0:  # Strict ordering
                graph[from_e].append(to_e)
                in_degree[to_e] += 1
        
        # Find one valid ordering
        queue = deque([e for e in self.events if in_degree[e] == 0])
        ordering = []
        
        while queue:
            current = queue.popleft()
            ordering.append(current)
            
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        return [ordering] if len(ordering) == len(self.events) else []


class CausalGraph:
    """Directed acyclic graph of causal relationships."""
    
    def __init__(self):
        self.links: List[CausalLink] = []
        self.nodes: Set[str] = set()
    
    def add_link(self, link: CausalLink):
        """Add causal link."""
        self.links.append(link)
        self.nodes.add(link.cause)
        self.nodes.add(link.effect)
    
    def get_causes(self, event_id: str, transitive: bool = False) -> List[str]:
        """Get direct or transitive causes of event."""
        if not transitive:
            return [link.cause for link in self.links if link.effect == event_id]
        
        # BFS for transitive closure
        causes = set()
        queue = deque([event_id])
        visited = set()
        
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            
            for link in self.links:
                if link.effect == current and link.cause not in visited:
                    causes.add(link.cause)
                    queue.append(link.cause)
        
        return list(causes)
    
    def get_effects(self, event_id: str, transitive: bool = False) -> List[str]:
        """Get direct or transitive effects of event."""
        if not transitive:
            return [link.effect for link in self.links if link.cause == event_id]
        
        # BFS for transitive closure
        effects = set()
        queue = deque([event_id])
        visited = set()
        
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            
            for link in self.links:
                if link.cause == current and link.effect not in visited:
                    effects.add(link.effect)
                    queue.append(link.effect)
        
        return list(effects)
    
    def find_root_causes(self) -> List[str]:
        """Find events with no predecessors."""
        has_predecessor = {link.effect for link in self.links}
        return [node for node in self.nodes if node not in has_predecessor]
    
    def intervene(self, event_id: str, new_value: Any) -> CausalGraph:
        """Perform causal intervention (do-calculus)."""
        # Create new graph with intervention
        new_graph = CausalGraph()
        new_graph.nodes = self.nodes.copy()
        
        # Remove all incoming edges to intervened variable
        for link in self.links:
            if link.effect != event_id:
                new_graph.add_link(link)
        
        return new_graph


class CounterfactualAnalyzer:
    """Analyze counterfactual scenarios."""
    
    def __init__(self, events: List[TemporalEvent], causal_graph: CausalGraph):
        self.events = {e.event_id: e for e in events}
        self.causal_graph = causal_graph
    
    def counterfactual(self, event_id: str, hypothetical_value: Any) -> Dict[str, Any]:
        """Analyze 'what if' scenario."""
        # Get all effects of this event
        affected = self.causal_graph.get_effects(event_id, transitive=True)
        
        # Simulate change propagation
        changes = {event_id: hypothetical_value}
        
        for affected_id in affected:
            # Simplified: propagate change with uncertainty decay
            link = next((l for l in self.causal_graph.links if l.effect == affected_id), None)
            if link:
                changes[affected_id] = f"affected_by_{event_id}"
        
        return {
            'original_event': event_id,
            'hypothetical': hypothetical_value,
            'affected_events': affected,
            'predicted_changes': changes
        }
    
    def necessity_sufficiency(self, cause_id: str, effect_id: str) -> Dict[str, float]:
        """Compute necessity and sufficiency of causal relationship."""
        # Necessity: P(not effect | not cause)
        # Sufficiency: P(effect | cause)
        # Simplified heuristic based on graph structure
        
        is_direct = any(l.cause == cause_id and l.effect == effect_id for l in self.causal_graph.links)
        all_causes = self.causal_graph.get_causes(effect_id, transitive=False)
        
        # Simple heuristics
        necessity = 1.0 if len(all_causes) == 1 and is_direct else 0.5
        sufficiency = 0.8 if is_direct else 0.3
        
        return {
            'necessity': necessity,
            'sufficiency': sufficiency,
            'is_direct': is_direct
        }


class TimelineSimulator:
    """Simulate alternate timelines."""
    
    def __init__(self):
        self.timelines: Dict[str, List[TemporalEvent]] = {'base': []}
        
    def add_event(self, event: TemporalEvent, timeline_id: str = 'base'):
        """Add event to timeline."""
        if timeline_id not in self.timelines:
            self.timelines[timeline_id] = []
        self.timelines[timeline_id].append(event)
    
    def fork_timeline(self, base_timeline: str, new_timeline: str, 
                     fork_point: datetime) -> str:
        """Create alternate timeline from fork point."""
        if base_timeline not in self.timelines:
            return None
        
        # Copy events before fork point
        base_events = self.timelines[base_timeline]
        forked = [e for e in base_events if e.start_time < fork_point]
        self.timelines[new_timeline] = forked
        
        return new_timeline
    
    def simulate_forward(self, timeline_id: str, duration: timedelta, 
                        rules: Optional[List[Callable]] = None) -> List[TemporalEvent]:
        """Simulate timeline forward."""
        if timeline_id not in self.timelines:
            return []
        
        events = self.timelines[timeline_id].copy()
        current_time = max(e.start_time for e in events) if events else datetime.utcnow()
        end_time = current_time + duration
        
        # Apply simulation rules
        if rules:
            while current_time < end_time:
                for rule in rules:
                    new_event = rule(events, current_time)
                    if new_event:
                        events.append(new_event)
                
                current_time += timedelta(seconds=1)
        
        return events
    
    def compare_timelines(self, timeline1: str, timeline2: str) -> Dict[str, Any]:
        """Compare two timelines."""
        events1 = set(e.event_id for e in self.timelines.get(timeline1, []))
        events2 = set(e.event_id for e in self.timelines.get(timeline2, []))
        
        return {
            'only_in_timeline1': list(events1 - events2),
            'only_in_timeline2': list(events2 - events1),
            'shared': list(events1 & events2),
            'divergence_count': len(events1.symmetric_difference(events2))
        }


class TemporalReasoner:
    """Main temporal reasoning orchestrator."""
    
    def __init__(self, conn):
        self.conn = conn
        self.events: Dict[str, TemporalEvent] = {}
        self.causal_graph = CausalGraph()
        self.constraint_network = TemporalConstraintNetwork()
        self.simulator = TimelineSimulator()
        self._init_db()
    
    def _init_db(self):
        cur = self.conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS temporal_events (
                event_id TEXT PRIMARY KEY,
                start_time TEXT NOT NULL,
                end_time TEXT,
                event_type TEXT,
                attributes TEXT,
                caused_by TEXT,
                effects TEXT,
                confidence REAL
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS causal_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cause TEXT NOT NULL,
                effect TEXT NOT NULL,
                strength REAL,
                delay_seconds REAL,
                mechanism TEXT
            )
        ''')
        self.conn.commit()
    
    def add_event(self, event: TemporalEvent):
        """Register temporal event."""
        self.events[event.event_id] = event
        self.simulator.add_event(event)
        
        # Persist
        cur = self.conn.cursor()
        cur.execute('''
            INSERT OR REPLACE INTO temporal_events 
            (event_id, start_time, end_time, event_type, attributes, caused_by, effects, confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            event.event_id,
            event.start_time.isoformat(),
            event.end_time.isoformat() if event.end_time else None,
            event.event_type,
            json.dumps(event.attributes),
            json.dumps(event.caused_by),
            json.dumps(event.effects),
            event.confidence
        ))
        self.conn.commit()
    
    def add_causal_link(self, link: CausalLink):
        """Add causal relationship."""
        self.causal_graph.add_link(link)
        
        # Update event references
        if link.cause in self.events:
            self.events[link.cause].effects.append(link.effect)
        if link.effect in self.events:
            self.events[link.effect].caused_by.append(link.cause)
        
        # Persist
        cur = self.conn.cursor()
        cur.execute('''
            INSERT INTO causal_links (cause, effect, strength, delay_seconds, mechanism)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            link.cause,
            link.effect,
            link.strength,
            link.delay.total_seconds() if link.delay else None,
            link.mechanism
        ))
        self.conn.commit()
    
    def infer_causality(self, event1_id: str, event2_id: str) -> Optional[float]:
        """Infer causal strength between events."""
        if event1_id not in self.events or event2_id not in self.events:
            return None
        
        e1 = self.events[event1_id]
        e2 = self.events[event2_id]
        
        # Temporal precedence required
        if e1.start_time >= e2.start_time:
            return 0.0
        
        # Heuristics
        time_gap = (e2.start_time - e1.start_time).total_seconds()
        
        # Closer in time = stronger causality (with decay)
        temporal_score = 1.0 / (1.0 + time_gap / 3600.0)  # Decay over hours
        
        # Check for attribute correlation
        correlation_score = 0.5  # Placeholder
        
        return (temporal_score + correlation_score) / 2.0
    
    def explain_event(self, event_id: str) -> Dict[str, Any]:
        """Generate causal explanation for event."""
        if event_id not in self.events:
            return {}
        
        event = self.events[event_id]
        causes = self.causal_graph.get_causes(event_id, transitive=True)
        effects = self.causal_graph.get_effects(event_id, transitive=True)
        root_causes = [c for c in causes if c in self.causal_graph.find_root_causes()]
        
        return {
            'event': event.event_id,
            'type': event.event_type,
            'time': event.start_time.isoformat(),
            'direct_causes': event.caused_by,
            'all_causes': causes,
            'root_causes': root_causes,
            'direct_effects': event.effects,
            'all_effects': effects,
            'explanation': f"Event {event_id} was caused by {len(causes)} factors and led to {len(effects)} outcomes."
        }
    
    def run_counterfactual(self, event_id: str, hypothetical: Any) -> Dict[str, Any]:
        """Run counterfactual analysis."""
        analyzer = CounterfactualAnalyzer(list(self.events.values()), self.causal_graph)
        return analyzer.counterfactual(event_id, hypothetical)
    
    def predict_future(self, horizon: timedelta) -> List[TemporalEvent]:
        """Predict future events based on causal patterns."""
        # Simple prediction: extrapolate patterns
        recent_events = sorted(
            self.events.values(),
            key=lambda e: e.start_time,
            reverse=True
        )[:10]
        
        predictions = []
        current_time = datetime.utcnow()
        
        for event in recent_events[:3]:
            # Predict similar event in future
            predicted = TemporalEvent(
                event_id=f"predicted_{event.event_id}_{current_time.timestamp()}",
                start_time=current_time + horizon / 2,
                event_type=event.event_type,
                confidence=0.6
            )
            predictions.append(predicted)
        
        return predictions
