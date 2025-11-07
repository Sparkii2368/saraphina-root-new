#!/usr/bin/env python3
"""
Consensus Engine: Reconcile divergent states across shadow nodes via majority voting.
Features: State comparison, divergence detection, conflict resolution, quorum-based decisions.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple, Set
from datetime import datetime
from dataclasses import dataclass, field
from collections import Counter
import json
import hashlib


@dataclass
class NodeState:
    """State of a single node."""
    node_id: str
    version: int
    state_hash: str
    data: Dict[str, Any]
    timestamp: datetime
    confidence: float = 1.0


@dataclass
class ConsensusProposal:
    """Proposal for consensus state."""
    proposal_id: str
    proposed_state: Dict[str, Any]
    supporting_nodes: List[str]
    vote_count: int
    confidence: float
    rationale: str


@dataclass
class DivergenceReport:
    """Report of state divergence."""
    timestamp: datetime
    total_nodes: int
    divergent_nodes: List[str]
    common_state: Optional[Dict[str, Any]]
    conflicts: List[Dict[str, Any]]
    resolution_needed: bool


class StateComparator:
    """Compare and diff node states."""
    
    @staticmethod
    def calculate_state_hash(data: Dict[str, Any]) -> str:
        """Calculate hash of state data."""
        # Sort keys for consistent hashing
        normalized = json.dumps(data, sort_keys=True)
        return hashlib.sha256(normalized.encode()).hexdigest()
    
    @staticmethod
    def compare_states(state1: NodeState, state2: NodeState) -> Dict[str, Any]:
        """Compare two node states."""
        comparison = {
            'identical': state1.state_hash == state2.state_hash,
            'version_diff': state2.version - state1.version,
            'time_diff_seconds': (state2.timestamp - state1.timestamp).total_seconds(),
            'conflicts': []
        }
        
        if not comparison['identical']:
            # Find conflicting keys
            all_keys = set(state1.data.keys()) | set(state2.data.keys())
            
            for key in all_keys:
                val1 = state1.data.get(key)
                val2 = state2.data.get(key)
                
                if val1 != val2:
                    comparison['conflicts'].append({
                        'key': key,
                        'node1_value': val1,
                        'node2_value': val2
                    })
        
        return comparison
    
    @staticmethod
    def find_common_state(states: List[NodeState]) -> Optional[Dict[str, Any]]:
        """Find most common state across nodes."""
        if not states:
            return None
        
        # Group by hash
        hash_groups = {}
        for state in states:
            if state.state_hash not in hash_groups:
                hash_groups[state.state_hash] = []
            hash_groups[state.state_hash].append(state)
        
        # Find largest group
        largest_group = max(hash_groups.values(), key=len)
        
        # Return if majority
        if len(largest_group) > len(states) / 2:
            return largest_group[0].data
        
        return None


class ConflictResolver:
    """Resolve conflicts between divergent states."""
    
    @staticmethod
    def resolve_by_majority(states: List[NodeState], key: str) -> Any:
        """Resolve conflict by majority vote."""
        values = [state.data.get(key) for state in states if key in state.data]
        
        if not values:
            return None
        
        # Count occurrences
        value_counts = Counter(json.dumps(v, sort_keys=True) for v in values)
        most_common_json = value_counts.most_common(1)[0][0]
        
        return json.loads(most_common_json)
    
    @staticmethod
    def resolve_by_newest(states: List[NodeState], key: str) -> Any:
        """Resolve conflict by using newest value."""
        states_with_key = [s for s in states if key in s.data]
        
        if not states_with_key:
            return None
        
        newest = max(states_with_key, key=lambda s: s.timestamp)
        return newest.data[key]
    
    @staticmethod
    def resolve_by_highest_version(states: List[NodeState], key: str) -> Any:
        """Resolve conflict using highest version."""
        states_with_key = [s for s in states if key in s.data]
        
        if not states_with_key:
            return None
        
        highest_version = max(states_with_key, key=lambda s: s.version)
        return highest_version.data[key]
    
    @staticmethod
    def resolve_by_confidence(states: List[NodeState], key: str) -> Any:
        """Resolve conflict using node confidence scores."""
        states_with_key = [s for s in states if key in s.data]
        
        if not states_with_key:
            return None
        
        highest_confidence = max(states_with_key, key=lambda s: s.confidence)
        return highest_confidence.data[key]
    
    @staticmethod
    def merge_states(states: List[NodeState], strategy: str = 'majority') -> Dict[str, Any]:
        """Merge multiple states using specified strategy."""
        if not states:
            return {}
        
        # Collect all keys
        all_keys = set()
        for state in states:
            all_keys.update(state.data.keys())
        
        merged = {}
        
        for key in all_keys:
            if strategy == 'majority':
                merged[key] = ConflictResolver.resolve_by_majority(states, key)
            elif strategy == 'newest':
                merged[key] = ConflictResolver.resolve_by_newest(states, key)
            elif strategy == 'highest_version':
                merged[key] = ConflictResolver.resolve_by_highest_version(states, key)
            elif strategy == 'confidence':
                merged[key] = ConflictResolver.resolve_by_confidence(states, key)
            else:
                # Default to majority
                merged[key] = ConflictResolver.resolve_by_majority(states, key)
        
        return merged


class QuorumManager:
    """Manage quorum requirements for consensus."""
    
    def __init__(self, required_quorum: float = 0.51):
        self.required_quorum = required_quorum  # 51% by default
    
    def has_quorum(self, votes: int, total_nodes: int) -> bool:
        """Check if quorum is reached."""
        if total_nodes == 0:
            return False
        return votes / total_nodes >= self.required_quorum
    
    def calculate_quorum_size(self, total_nodes: int) -> int:
        """Calculate minimum votes needed for quorum."""
        return int(total_nodes * self.required_quorum) + 1


class ConsensusEngine:
    """Main consensus orchestrator."""
    
    def __init__(self, quorum: float = 0.51):
        self.comparator = StateComparator()
        self.resolver = ConflictResolver()
        self.quorum_manager = QuorumManager(quorum)
        self.consensus_history: List[Dict[str, Any]] = []
    
    def detect_divergence(self, node_states: List[NodeState]) -> DivergenceReport:
        """Detect divergence across nodes."""
        if not node_states:
            return DivergenceReport(
                timestamp=datetime.utcnow(),
                total_nodes=0,
                divergent_nodes=[],
                common_state=None,
                conflicts=[],
                resolution_needed=False
            )
        
        # Group by hash
        hash_groups = {}
        for state in node_states:
            if state.state_hash not in hash_groups:
                hash_groups[state.state_hash] = []
            hash_groups[state.state_hash].append(state.node_id)
        
        # Check if all nodes agree
        if len(hash_groups) == 1:
            return DivergenceReport(
                timestamp=datetime.utcnow(),
                total_nodes=len(node_states),
                divergent_nodes=[],
                common_state=node_states[0].data,
                conflicts=[],
                resolution_needed=False
            )
        
        # Find common state
        common_state = self.comparator.find_common_state(node_states)
        
        # Identify divergent nodes
        if common_state:
            common_hash = self.comparator.calculate_state_hash(common_state)
            divergent_nodes = [
                state.node_id for state in node_states 
                if state.state_hash != common_hash
            ]
        else:
            # No majority - all nodes divergent
            divergent_nodes = [state.node_id for state in node_states]
        
        # Analyze conflicts
        conflicts = []
        if len(node_states) >= 2:
            base_state = node_states[0]
            for other_state in node_states[1:]:
                comparison = self.comparator.compare_states(base_state, other_state)
                if comparison['conflicts']:
                    conflicts.extend(comparison['conflicts'])
        
        return DivergenceReport(
            timestamp=datetime.utcnow(),
            total_nodes=len(node_states),
            divergent_nodes=divergent_nodes,
            common_state=common_state,
            conflicts=conflicts,
            resolution_needed=len(divergent_nodes) > 0
        )
    
    def propose_consensus(self, node_states: List[NodeState], 
                         strategy: str = 'majority') -> ConsensusProposal:
        """Generate consensus proposal."""
        # Merge states using strategy
        merged_state = self.resolver.merge_states(node_states, strategy)
        merged_hash = self.comparator.calculate_state_hash(merged_state)
        
        # Count supporting nodes
        supporting_nodes = [
            state.node_id for state in node_states 
            if state.state_hash == merged_hash
        ]
        
        # If no exact matches, count how many would support merged state
        if not supporting_nodes:
            supporting_nodes = [state.node_id for state in node_states]
        
        # Calculate confidence
        confidence = len(supporting_nodes) / len(node_states) if node_states else 0
        
        proposal = ConsensusProposal(
            proposal_id=f"proposal_{datetime.utcnow().timestamp()}",
            proposed_state=merged_state,
            supporting_nodes=supporting_nodes,
            vote_count=len(supporting_nodes),
            confidence=confidence,
            rationale=f"Merged using {strategy} strategy from {len(node_states)} nodes"
        )
        
        return proposal
    
    def reach_consensus(self, node_states: List[NodeState], 
                       strategy: str = 'majority',
                       require_quorum: bool = True) -> Tuple[bool, Optional[ConsensusProposal]]:
        """Attempt to reach consensus."""
        if not node_states:
            return False, None
        
        # Generate proposal
        proposal = self.propose_consensus(node_states, strategy)
        
        # Check quorum
        has_quorum = self.quorum_manager.has_quorum(
            proposal.vote_count,
            len(node_states)
        )
        
        if require_quorum and not has_quorum:
            return False, proposal
        
        # Record consensus
        self.consensus_history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'proposal_id': proposal.proposal_id,
            'strategy': strategy,
            'vote_count': proposal.vote_count,
            'total_nodes': len(node_states),
            'confidence': proposal.confidence,
            'reached_consensus': True
        })
        
        return True, proposal
    
    def reconcile_states(self, divergence: DivergenceReport, 
                        node_states: List[NodeState],
                        owner_confirmation: bool = False) -> Dict[str, Any]:
        """Reconcile divergent states."""
        reconciliation = {
            'timestamp': datetime.utcnow().isoformat(),
            'divergence_detected': divergence.resolution_needed,
            'reconciliation_performed': False,
            'final_state': None,
            'applied_to_nodes': []
        }
        
        if not divergence.resolution_needed:
            reconciliation['final_state'] = divergence.common_state
            reconciliation['reconciliation_performed'] = False
            return reconciliation
        
        # If owner confirmation required and not provided, return proposal
        if owner_confirmation:
            # Try multiple strategies
            strategies = ['majority', 'newest', 'highest_version', 'confidence']
            proposals = []
            
            for strategy in strategies:
                success, proposal = self.reach_consensus(
                    node_states,
                    strategy=strategy,
                    require_quorum=True
                )
                
                if success:
                    proposals.append({
                        'strategy': strategy,
                        'proposal': proposal,
                        'confidence': proposal.confidence
                    })
            
            reconciliation['proposals'] = proposals
            reconciliation['requires_owner_confirmation'] = True
            return reconciliation
        
        # Automatic reconciliation
        success, proposal = self.reach_consensus(
            node_states,
            strategy='majority',
            require_quorum=True
        )
        
        if success:
            reconciliation['reconciliation_performed'] = True
            reconciliation['final_state'] = proposal.proposed_state
            reconciliation['applied_to_nodes'] = proposal.supporting_nodes
            reconciliation['confidence'] = proposal.confidence
        else:
            reconciliation['error'] = 'Could not reach quorum for automatic reconciliation'
        
        return reconciliation
    
    def validate_recovery(self, recovered_state: Dict[str, Any], 
                         reference_states: List[NodeState]) -> Dict[str, Any]:
        """Validate recovered state against reference states."""
        recovered_hash = self.comparator.calculate_state_hash(recovered_state)
        
        validation = {
            'valid': False,
            'confidence': 0.0,
            'matching_nodes': [],
            'conflicts': []
        }
        
        # Check how many reference states match
        for ref_state in reference_states:
            if ref_state.state_hash == recovered_hash:
                validation['matching_nodes'].append(ref_state.node_id)
        
        # Calculate confidence
        if reference_states:
            validation['confidence'] = len(validation['matching_nodes']) / len(reference_states)
            validation['valid'] = validation['confidence'] >= 0.5  # 50% threshold
        
        # Find conflicts
        if not validation['valid'] and reference_states:
            # Compare with most common state
            common_state = self.comparator.find_common_state(reference_states)
            if common_state:
                recovered_node_state = NodeState(
                    node_id='recovered',
                    version=0,
                    state_hash=recovered_hash,
                    data=recovered_state,
                    timestamp=datetime.utcnow()
                )
                
                common_node_state = NodeState(
                    node_id='common',
                    version=0,
                    state_hash=self.comparator.calculate_state_hash(common_state),
                    data=common_state,
                    timestamp=datetime.utcnow()
                )
                
                comparison = self.comparator.compare_states(recovered_node_state, common_node_state)
                validation['conflicts'] = comparison['conflicts']
        
        return validation
    
    def get_consensus_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent consensus history."""
        return self.consensus_history[-limit:]
