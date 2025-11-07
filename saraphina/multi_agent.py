#!/usr/bin/env python3
"""
MultiAgent: task delegation, sub-agent lifecycle, result aggregation.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

class SubAgent:
    def __init__(self, agent_id: str, task: str):
        self.id = agent_id
        self.task = task
        self.status = 'pending'
        self.result = None

    def execute(self) -> Any:
        # Simulate task execution (replace with actual logic)
        self.status = 'running'
        try:
            # Example: parse task and execute
            if 'research' in self.task.lower():
                self.result = {'summary': f'Research on {self.task}', 'sources': 3}
            elif 'analyze' in self.task.lower():
                self.result = {'analysis': f'Analysis of {self.task}', 'score': 0.8}
            else:
                self.result = {'output': f'Completed {self.task}'}
            self.status = 'completed'
        except Exception as e:
            self.status = 'failed'
            self.result = {'error': str(e)}
        return self.result


class MultiAgentCoordinator:
    def __init__(self, conn):
        self.conn = conn
        self.agents: Dict[str, SubAgent] = {}

    def spawn(self, task: str) -> str:
        from uuid import uuid4
        aid = str(uuid4())
        agent = SubAgent(aid, task)
        self.agents[aid] = agent
        return aid

    def execute_parallel(self, tasks: List[str]) -> List[Dict[str, Any]]:
        aids = [self.spawn(t) for t in tasks]
        results = []
        for aid in aids:
            agent = self.agents[aid]
            result = agent.execute()
            results.append({'task': agent.task, 'status': agent.status, 'result': result})
        return results

    def consensus(self, results: List[Dict[str, Any]], strategy: str = 'majority') -> Any:
        # Aggregate results
        if strategy == 'majority':
            # Count most common result
            counts = {}
            for r in results:
                key = json.dumps(r.get('result'), sort_keys=True)
                counts[key] = counts.get(key, 0) + 1
            return json.loads(max(counts, key=counts.get)) if counts else None
        elif strategy == 'average':
            # Average numeric results
            scores = [r.get('result', {}).get('score', 0) for r in results if isinstance(r.get('result'), dict)]
            return sum(scores) / len(scores) if scores else 0
        return results[0]['result'] if results else None
