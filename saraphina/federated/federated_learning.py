"""
Federated Intelligence System
Privacy-preserving federated learning, cross-user pattern sharing, swarm coordination
"""
import hashlib
import json
import numpy as np
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import time
import secrets


@dataclass
class FederatedModel:
    """Federated learning model"""
    model_id: str
    model_type: str  # recovery_strategy, movement_pattern, risk_assessment
    global_weights: Dict[str, List[float]]
    version: int
    last_updated: float
    num_contributors: int
    accuracy_metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class LocalUpdate:
    """Local model update from a client"""
    update_id: str
    model_id: str
    client_id_hash: str  # Anonymized client ID
    local_weights: Dict[str, List[float]]
    num_samples: int
    timestamp: float
    privacy_budget: float  # Differential privacy epsilon


class FederatedLearningCoordinator:
    """Coordinates federated learning across devices"""
    
    def __init__(self, privacy_budget: float = 1.0):
        self.models: Dict[str, FederatedModel] = {}
        self.pending_updates: List[LocalUpdate] = []
        self.privacy_budget = privacy_budget
        self.aggregation_threshold = 5  # Min clients before aggregation
        
    def create_model(self, model_type: str, initial_weights: Optional[Dict] = None) -> str:
        """Create new federated model"""
        model_id = f"fed-model-{secrets.token_hex(8)}"
        
        self.models[model_id] = FederatedModel(
            model_id=model_id,
            model_type=model_type,
            global_weights=initial_weights or {},
            version=1,
            last_updated=time.time(),
            num_contributors=0
        )
        
        return model_id
    
    def submit_local_update(self, model_id: str, client_id: str, 
                           local_weights: Dict, num_samples: int) -> str:
        """Submit local model update with differential privacy"""
        if model_id not in self.models:
            raise ValueError(f"Model {model_id} not found")
        
        # Anonymize client ID
        client_id_hash = hashlib.sha256(client_id.encode()).hexdigest()[:16]
        
        # Add noise for differential privacy
        noisy_weights = self._add_privacy_noise(local_weights, self.privacy_budget)
        
        update = LocalUpdate(
            update_id=f"update-{secrets.token_hex(8)}",
            model_id=model_id,
            client_id_hash=client_id_hash,
            local_weights=noisy_weights,
            num_samples=num_samples,
            timestamp=time.time(),
            privacy_budget=self.privacy_budget
        )
        
        self.pending_updates.append(update)
        
        # Trigger aggregation if threshold reached
        if len([u for u in self.pending_updates if u.model_id == model_id]) >= self.aggregation_threshold:
            self.aggregate_updates(model_id)
        
        return update.update_id
    
    def _add_privacy_noise(self, weights: Dict, epsilon: float) -> Dict:
        """Add Laplacian noise for differential privacy"""
        noisy_weights = {}
        sensitivity = 1.0  # L1 sensitivity
        scale = sensitivity / epsilon
        
        for key, values in weights.items():
            noise = np.random.laplace(0, scale, len(values))
            noisy_weights[key] = (np.array(values) + noise).tolist()
        
        return noisy_weights
    
    def aggregate_updates(self, model_id: str):
        """Federated averaging (FedAvg) aggregation"""
        model = self.models.get(model_id)
        if not model:
            return
        
        # Get pending updates for this model
        updates = [u for u in self.pending_updates if u.model_id == model_id]
        if not updates:
            return
        
        # Weighted average by number of samples
        total_samples = sum(u.num_samples for u in updates)
        new_weights = {}
        
        # Get all weight keys
        all_keys = set()
        for update in updates:
            all_keys.update(update.local_weights.keys())
        
        # Aggregate each weight
        for key in all_keys:
            weighted_sum = np.zeros(len(updates[0].local_weights.get(key, [])))
            
            for update in updates:
                if key in update.local_weights:
                    weight_contribution = np.array(update.local_weights[key]) * (update.num_samples / total_samples)
                    weighted_sum += weight_contribution
            
            new_weights[key] = weighted_sum.tolist()
        
        # Update global model
        model.global_weights = new_weights
        model.version += 1
        model.last_updated = time.time()
        model.num_contributors += len(updates)
        
        # Clear processed updates
        self.pending_updates = [u for u in self.pending_updates if u.model_id != model_id]
        
        print(f"Aggregated {len(updates)} updates for model {model_id} (v{model.version})")
    
    def get_global_model(self, model_id: str) -> Optional[FederatedModel]:
        """Retrieve global model for client download"""
        return self.models.get(model_id)
    
    def secure_aggregation(self, model_id: str):
        """Secure multi-party computation aggregation (advanced)"""
        # In production: implement secure aggregation protocol
        # where server never sees individual updates
        pass


class SwarmCoordinator:
    """Coordinates multi-device swarm behavior"""
    
    def __init__(self):
        self.swarms: Dict[str, Dict] = {}
        self.device_assignments: Dict[str, str] = {}  # device_id -> swarm_id
    
    def create_swarm(self, target_device_id: str, scout_device_ids: List[str]) -> str:
        """Create device swarm for collaborative search"""
        swarm_id = f"swarm-{secrets.token_hex(8)}"
        
        self.swarms[swarm_id] = {
            "swarm_id": swarm_id,
            "target_device": target_device_id,
            "scouts": scout_device_ids,
            "created_at": time.time(),
            "status": "active",
            "search_grid": self._generate_search_grid(target_device_id),
            "assignments": {}
        }
        
        # Assign scouts to grid cells
        grid = self.swarms[swarm_id]["search_grid"]
        for i, scout_id in enumerate(scout_device_ids):
            cell = grid[i % len(grid)]
            self.swarms[swarm_id]["assignments"][scout_id] = cell
            self.device_assignments[scout_id] = swarm_id
        
        return swarm_id
    
    def _generate_search_grid(self, target_device_id: str) -> List[Dict]:
        """Generate search grid around target last known location"""
        # Mock implementation
        # In production: divide area into cells based on last known location
        base_lat, base_lon = 37.7749, -122.4194
        grid_size = 0.01  # ~1km cells
        
        grid = []
        for i in range(-2, 3):
            for j in range(-2, 3):
                grid.append({
                    "cell_id": f"cell-{i}-{j}",
                    "center": (base_lat + i * grid_size, base_lon + j * grid_size),
                    "radius_km": 0.5
                })
        
        return grid
    
    def report_scout_position(self, scout_device_id: str, location: tuple):
        """Scout device reports current position"""
        swarm_id = self.device_assignments.get(scout_device_id)
        if not swarm_id or swarm_id not in self.swarms:
            return
        
        swarm = self.swarms[swarm_id]
        assigned_cell = swarm["assignments"].get(scout_device_id)
        
        # Check if scout reached assigned cell
        # In production: implement proximity check
        print(f"Scout {scout_device_id} at {location}, assigned to {assigned_cell}")
    
    def report_target_found(self, scout_device_id: str, target_location: tuple):
        """Scout reports target device found"""
        swarm_id = self.device_assignments.get(scout_device_id)
        if not swarm_id:
            return
        
        swarm = self.swarms[swarm_id]
        swarm["status"] = "success"
        swarm["found_location"] = target_location
        swarm["found_by"] = scout_device_id
        swarm["completed_at"] = time.time()
        
        # Recall all scouts
        self._recall_swarm(swarm_id)
        
        print(f"✓ Target found by {scout_device_id} at {target_location}")
    
    def _recall_swarm(self, swarm_id: str):
        """Recall all scouts from swarm"""
        swarm = self.swarms.get(swarm_id)
        if not swarm:
            return
        
        for scout_id in swarm["scouts"]:
            if scout_id in self.device_assignments:
                del self.device_assignments[scout_id]
        
        print(f"Swarm {swarm_id} recalled")


class PatternSharingService:
    """Anonymous pattern sharing across users"""
    
    def __init__(self):
        self.shared_patterns: List[Dict] = []
        self.pattern_index: Dict[str, List[int]] = {}
    
    def share_pattern(self, pattern_type: str, pattern_data: Dict, 
                     success_rate: float, anonymize: bool = True) -> str:
        """Share recovery pattern anonymously"""
        pattern_id = f"pattern-{secrets.token_hex(8)}"
        
        if anonymize:
            pattern_data = self._anonymize_pattern(pattern_data)
        
        pattern = {
            "pattern_id": pattern_id,
            "pattern_type": pattern_type,
            "data": pattern_data,
            "success_rate": success_rate,
            "usage_count": 0,
            "shared_at": time.time()
        }
        
        self.shared_patterns.append(pattern)
        
        # Index by type
        if pattern_type not in self.pattern_index:
            self.pattern_index[pattern_type] = []
        self.pattern_index[pattern_type].append(len(self.shared_patterns) - 1)
        
        return pattern_id
    
    def _anonymize_pattern(self, pattern_data: Dict) -> Dict:
        """Remove PII from pattern data"""
        anonymized = pattern_data.copy()
        
        # Remove exact locations (keep general area)
        if "location" in anonymized:
            lat, lon = anonymized["location"]
            # Round to ~10km precision
            anonymized["location"] = (round(lat, 1), round(lon, 1))
        
        # Remove identifiable fields
        for key in ["user_id", "device_id", "name", "email"]:
            anonymized.pop(key, None)
        
        return anonymized
    
    def query_patterns(self, pattern_type: str, min_success_rate: float = 0.5) -> List[Dict]:
        """Query shared patterns by type"""
        if pattern_type not in self.pattern_index:
            return []
        
        indices = self.pattern_index[pattern_type]
        patterns = [self.shared_patterns[i] for i in indices]
        
        # Filter by success rate
        patterns = [p for p in patterns if p["success_rate"] >= min_success_rate]
        
        # Sort by success rate
        patterns.sort(key=lambda x: x["success_rate"], reverse=True)
        
        return patterns
    
    def report_pattern_usage(self, pattern_id: str, success: bool):
        """Report pattern usage for crowd-sourced validation"""
        pattern = next((p for p in self.shared_patterns if p["pattern_id"] == pattern_id), None)
        if not pattern:
            return
        
        pattern["usage_count"] += 1
        
        # Update success rate with Bayesian update
        old_rate = pattern["success_rate"]
        old_count = pattern["usage_count"] - 1
        
        # Weighted average
        new_rate = (old_rate * old_count + (1.0 if success else 0.0)) / pattern["usage_count"]
        pattern["success_rate"] = new_rate


# Global instances
_fed_coordinator = None
_swarm_coordinator = None
_pattern_service = None

def get_federated_coordinator() -> FederatedLearningCoordinator:
    global _fed_coordinator
    if _fed_coordinator is None:
        _fed_coordinator = FederatedLearningCoordinator()
    return _fed_coordinator

def get_swarm_coordinator() -> SwarmCoordinator:
    global _swarm_coordinator
    if _swarm_coordinator is None:
        _swarm_coordinator = SwarmCoordinator()
    return _swarm_coordinator

def get_pattern_service() -> PatternSharingService:
    global _pattern_service
    if _pattern_service is None:
        _pattern_service = PatternSharingService()
    return _pattern_service
