#!/usr/bin/env python3
"""
Distributed Agent Mesh: Multi-node coordination with Raft consensus, gossip protocol, fault tolerance.
Features: Leader election, log replication, membership management, workload distribution, failure detection.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional, Set, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import random
import json
import time
import hashlib


class NodeState(Enum):
    FOLLOWER = "follower"
    CANDIDATE = "candidate"
    LEADER = "leader"


@dataclass
class LogEntry:
    """Replicated log entry for Raft consensus."""
    term: int
    index: int
    command: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def hash(self) -> str:
        """Generate hash for entry verification."""
        data = f"{self.term}:{self.index}:{json.dumps(self.command, sort_keys=True)}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]


@dataclass
class NodeInfo:
    """Information about a cluster node."""
    node_id: str
    address: str
    port: int
    state: NodeState = NodeState.FOLLOWER
    last_heartbeat: Optional[datetime] = None
    term: int = 0
    workload: float = 0.0  # Current workload 0-1
    capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class RaftConsensus:
    """Raft consensus algorithm for distributed coordination."""
    
    def __init__(self, node_id: str, peers: List[str]):
        self.node_id = node_id
        self.peers = peers
        self.state = NodeState.FOLLOWER
        self.current_term = 0
        self.voted_for: Optional[str] = None
        self.log: List[LogEntry] = []
        self.commit_index = 0
        self.last_applied = 0
        
        # Leader-specific state
        self.next_index: Dict[str, int] = {p: 1 for p in peers}
        self.match_index: Dict[str, int] = {p: 0 for p in peers}
        
        # Timing
        self.election_timeout = random.uniform(150, 300)  # ms
        self.last_heartbeat = time.time()
        
    def append_entries(self, term: int, leader_id: str, prev_log_index: int, 
                      prev_log_term: int, entries: List[LogEntry], 
                      leader_commit: int) -> tuple[bool, int]:
        """Handle AppendEntries RPC (heartbeat or log replication)."""
        
        # Reply false if term < currentTerm
        if term < self.current_term:
            return False, self.current_term
        
        # Update term and convert to follower
        if term > self.current_term:
            self.current_term = term
            self.state = NodeState.FOLLOWER
            self.voted_for = None
        
        self.last_heartbeat = time.time()
        
        # Reply false if log doesn't contain entry at prevLogIndex matching prevLogTerm
        if prev_log_index > 0:
            if prev_log_index > len(self.log) or self.log[prev_log_index - 1].term != prev_log_term:
                return False, self.current_term
        
        # Append new entries
        for i, entry in enumerate(entries):
            idx = prev_log_index + i + 1
            if idx <= len(self.log):
                if self.log[idx - 1].term != entry.term:
                    # Delete conflicting entry and all that follow
                    self.log = self.log[:idx - 1]
                    self.log.append(entry)
            else:
                self.log.append(entry)
        
        # Update commit index
        if leader_commit > self.commit_index:
            self.commit_index = min(leader_commit, len(self.log))
        
        return True, self.current_term
    
    def request_vote(self, term: int, candidate_id: str, 
                    last_log_index: int, last_log_term: int) -> tuple[bool, int]:
        """Handle RequestVote RPC."""
        
        # Reply false if term < currentTerm
        if term < self.current_term:
            return False, self.current_term
        
        # Update term
        if term > self.current_term:
            self.current_term = term
            self.voted_for = None
            self.state = NodeState.FOLLOWER
        
        # Check if already voted or log is more up-to-date
        if self.voted_for is None or self.voted_for == candidate_id:
            my_last_log_index = len(self.log)
            my_last_log_term = self.log[-1].term if self.log else 0
            
            if (last_log_term > my_last_log_term or 
                (last_log_term == my_last_log_term and last_log_index >= my_last_log_index)):
                self.voted_for = candidate_id
                self.last_heartbeat = time.time()
                return True, self.current_term
        
        return False, self.current_term
    
    def start_election(self) -> bool:
        """Start leader election."""
        self.state = NodeState.CANDIDATE
        self.current_term += 1
        self.voted_for = self.node_id
        votes_received = 1
        
        # Request votes from peers (simulated)
        # In real implementation, send RequestVote RPCs
        for peer in self.peers:
            # Simulate vote response
            if random.random() > 0.3:  # 70% success rate
                votes_received += 1
        
        # Check if won election
        if votes_received > (len(self.peers) + 1) // 2:
            self.state = NodeState.LEADER
            # Reinitialize leader state
            self.next_index = {p: len(self.log) + 1 for p in self.peers}
            self.match_index = {p: 0 for p in self.peers}
            return True
        
        return False
    
    def replicate_log(self, command: Dict[str, Any]) -> bool:
        """Replicate command to cluster (leader only)."""
        if self.state != NodeState.LEADER:
            return False
        
        # Append to local log
        entry = LogEntry(
            term=self.current_term,
            index=len(self.log) + 1,
            command=command
        )
        self.log.append(entry)
        
        # Replicate to majority (simulated)
        replicated = 1
        for peer in self.peers:
            if random.random() > 0.2:  # 80% success rate
                replicated += 1
        
        # Commit if replicated to majority
        if replicated > (len(self.peers) + 1) // 2:
            self.commit_index = len(self.log)
            return True
        
        return False


class GossipProtocol:
    """Membership and state dissemination via gossip."""
    
    def __init__(self, node_id: str, fanout: int = 3):
        self.node_id = node_id
        self.fanout = fanout
        self.members: Dict[str, NodeInfo] = {}
        self.version: Dict[str, int] = {}  # State version for each member
        
    def add_member(self, node_info: NodeInfo):
        """Add member to cluster."""
        self.members[node_info.node_id] = node_info
        self.version[node_info.node_id] = 0
    
    def remove_member(self, node_id: str):
        """Remove member from cluster."""
        self.members.pop(node_id, None)
        self.version.pop(node_id, None)
    
    def update_state(self, node_id: str, state: Dict[str, Any]):
        """Update state for a node."""
        if node_id in self.members:
            self.members[node_id].metadata.update(state)
            self.version[node_id] = self.version.get(node_id, 0) + 1
    
    def gossip_round(self) -> List[Dict[str, Any]]:
        """Perform one gossip round: select random peers and exchange state."""
        if not self.members:
            return []
        
        # Select random peers
        peers = random.sample(list(self.members.keys()), min(self.fanout, len(self.members)))
        
        messages = []
        for peer_id in peers:
            # Prepare gossip message with state updates
            msg = {
                'from': self.node_id,
                'to': peer_id,
                'members': {
                    nid: {
                        'state': n.state.value,
                        'term': n.term,
                        'workload': n.workload,
                        'version': self.version.get(nid, 0)
                    }
                    for nid, n in self.members.items()
                }
            }
            messages.append(msg)
        
        return messages
    
    def handle_gossip(self, message: Dict[str, Any]):
        """Process incoming gossip message."""
        from_node = message.get('from')
        received_members = message.get('members', {})
        
        # Merge state updates
        for node_id, state in received_members.items():
            received_version = state.get('version', 0)
            current_version = self.version.get(node_id, -1)
            
            if received_version > current_version:
                # Update to newer state
                if node_id in self.members:
                    self.members[node_id].workload = state.get('workload', 0.0)
                    self.members[node_id].term = state.get('term', 0)
                    self.version[node_id] = received_version
    
    def detect_failures(self, timeout_seconds: float = 30.0) -> List[str]:
        """Detect failed nodes based on heartbeat timeout."""
        now = datetime.utcnow()
        failed = []
        
        for node_id, info in self.members.items():
            if info.last_heartbeat:
                elapsed = (now - info.last_heartbeat).total_seconds()
                if elapsed > timeout_seconds:
                    failed.append(node_id)
        
        return failed


class WorkloadBalancer:
    """Distribute workload across cluster nodes."""
    
    def __init__(self, strategy: str = 'least_loaded'):
        self.strategy = strategy
        self.task_assignments: Dict[str, str] = {}  # task_id -> node_id
        
    def assign_task(self, task_id: str, task: Dict[str, Any], nodes: Dict[str, NodeInfo]) -> Optional[str]:
        """Assign task to optimal node."""
        if not nodes:
            return None
        
        if self.strategy == 'least_loaded':
            # Assign to node with lowest workload
            target = min(nodes.values(), key=lambda n: n.workload)
        elif self.strategy == 'round_robin':
            # Simple round-robin
            node_list = list(nodes.values())
            target = node_list[len(self.task_assignments) % len(node_list)]
        elif self.strategy == 'capability_match':
            # Match task requirements to node capabilities
            required_caps = task.get('capabilities', [])
            candidates = [n for n in nodes.values() if all(cap in n.capabilities for cap in required_caps)]
            target = min(candidates, key=lambda n: n.workload) if candidates else None
        else:
            target = random.choice(list(nodes.values()))
        
        if target:
            self.task_assignments[task_id] = target.node_id
            target.workload += task.get('weight', 0.1)
            return target.node_id
        
        return None
    
    def complete_task(self, task_id: str, nodes: Dict[str, NodeInfo], task_weight: float = 0.1):
        """Mark task as completed and update workload."""
        if task_id in self.task_assignments:
            node_id = self.task_assignments.pop(task_id)
            if node_id in nodes:
                nodes[node_id].workload = max(0.0, nodes[node_id].workload - task_weight)


class DistributedMesh:
    """Orchestrates distributed agent coordination."""
    
    def __init__(self, node_id: str, address: str = 'localhost', port: int = 8000):
        self.node_id = node_id
        self.node_info = NodeInfo(node_id, address, port)
        self.peers: Dict[str, NodeInfo] = {}
        
        # Subsystems
        self.raft = RaftConsensus(node_id, [])
        self.gossip = GossipProtocol(node_id)
        self.balancer = WorkloadBalancer(strategy='least_loaded')
        
    def join_cluster(self, peer_nodes: List[NodeInfo]):
        """Join existing cluster."""
        for peer in peer_nodes:
            self.peers[peer.node_id] = peer
            self.gossip.add_member(peer)
        
        self.raft.peers = list(self.peers.keys())
    
    def submit_command(self, command: Dict[str, Any]) -> bool:
        """Submit command to cluster (goes through leader)."""
        if self.raft.state == NodeState.LEADER:
            return self.raft.replicate_log(command)
        else:
            # Forward to leader (simulated)
            # In real impl: find leader and forward via RPC
            return False
    
    def distribute_task(self, task: Dict[str, Any]) -> Optional[str]:
        """Distribute task to optimal node in cluster."""
        task_id = task.get('id', f"task_{random.randint(1000, 9999)}")
        return self.balancer.assign_task(task_id, task, self.peers)
    
    def run_maintenance(self):
        """Periodic maintenance: gossip, failure detection, leader election."""
        # Gossip round
        messages = self.gossip.gossip_round()
        
        # Detect failures
        failed = self.gossip.detect_failures()
        for node_id in failed:
            self.gossip.remove_member(node_id)
            self.peers.pop(node_id, None)
        
        # Leader election if needed
        if self.raft.state == NodeState.FOLLOWER:
            elapsed = (time.time() - self.raft.last_heartbeat) * 1000
            if elapsed > self.raft.election_timeout:
                self.raft.start_election()
    
    def get_cluster_status(self) -> Dict[str, Any]:
        """Get current cluster status."""
        return {
            'node_id': self.node_id,
            'state': self.raft.state.value,
            'term': self.raft.current_term,
            'commit_index': self.raft.commit_index,
            'log_size': len(self.raft.log),
            'cluster_size': len(self.peers) + 1,
            'members': [
                {
                    'node_id': n.node_id,
                    'address': f"{n.address}:{n.port}",
                    'state': n.state.value,
                    'workload': n.workload,
                    'capabilities': n.capabilities
                }
                for n in self.peers.values()
            ]
        }
    
    def execute_distributed_query(self, query: str, aggregation: str = 'collect') -> List[Any]:
        """Execute query across all nodes and aggregate results."""
        results = []
        
        # Execute locally
        local_result = self._execute_query_locally(query)
        results.append(local_result)
        
        # Execute on peers (simulated)
        for peer in self.peers.values():
            # In real impl: send RPC to peer
            peer_result = {'node': peer.node_id, 'data': random.randint(1, 100)}
            results.append(peer_result)
        
        # Aggregate
        if aggregation == 'collect':
            return results
        elif aggregation == 'sum':
            return [sum(r.get('data', 0) for r in results)]
        elif aggregation == 'max':
            return [max(r.get('data', 0) for r in results)]
        elif aggregation == 'consensus':
            # Majority voting
            from collections import Counter
            values = [r.get('data') for r in results]
            return [Counter(values).most_common(1)[0][0]]
        
        return results
    
    def _execute_query_locally(self, query: str) -> Dict[str, Any]:
        """Execute query on local node."""
        return {'node': self.node_id, 'data': random.randint(1, 100)}
