"""
Advanced Recovery Methods
Bluetooth mesh, LoRa/LoRaWAN, UWB precision tracking, computer vision localization
"""
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import time
import math


@dataclass
class BLEMeshNode:
    """Bluetooth mesh network node"""
    node_id: str
    location: Tuple[float, float]
    rssi: int
    hop_count: int
    last_seen: float


class BLEMeshNetwork:
    """Bluetooth mesh networking for device recovery"""
    
    def __init__(self):
        self.nodes: Dict[str, BLEMeshNode] = {}
        self.mesh_routes: Dict[str, List[str]] = {}  # target -> [relay nodes]
    
    def add_node(self, node_id: str, location: Tuple[float, float], rssi: int):
        """Add node to mesh network"""
        self.nodes[node_id] = BLEMeshNode(
            node_id=node_id,
            location=location,
            rssi=rssi,
            hop_count=0,
            last_seen=time.time()
        )
    
    def discover_route(self, target_device_id: str) -> Optional[List[str]]:
        """Discover mesh route to target device"""
        # Simplified mesh routing (flooding)
        # In production: implement proper mesh protocols (BLE Mesh spec)
        
        if target_device_id not in self.nodes:
            return None
        
        # BFS to find shortest path
        visited = set()
        queue = [(target_device_id, [target_device_id])]
        
        while queue:
            current, path = queue.pop(0)
            if current in visited:
                continue
            
            visited.add(current)
            
            # Check if we reached a gateway
            if self._is_gateway(current):
                self.mesh_routes[target_device_id] = path
                return path
            
            # Add neighbors to queue
            for neighbor in self._get_neighbors(current):
                if neighbor not in visited:
                    queue.append((neighbor, path + [neighbor]))
        
        return None
    
    def _is_gateway(self, node_id: str) -> bool:
        """Check if node is mesh gateway"""
        # Mock: nodes with good RSSI are gateways
        node = self.nodes.get(node_id)
        return node and node.rssi > -60
    
    def _get_neighbors(self, node_id: str) -> List[str]:
        """Get mesh neighbors within range"""
        node = self.nodes.get(node_id)
        if not node:
            return []
        
        neighbors = []
        for other_id, other_node in self.nodes.items():
            if other_id == node_id:
                continue
            
            # Check if in range (~10m for BLE)
            dist = self._calculate_distance(node.location, other_node.location)
            if dist < 0.01:  # ~10m in degrees
                neighbors.append(other_id)
        
        return neighbors
    
    def _calculate_distance(self, loc1: Tuple[float, float], loc2: Tuple[float, float]) -> float:
        """Calculate distance between two coordinates"""
        lat1, lon1 = loc1
        lat2, lon2 = loc2
        return math.sqrt((lat2 - lat1)**2 + (lon2 - lon1)**2)
    
    def send_message(self, target_device_id: str, message: Dict) -> bool:
        """Send message through mesh network"""
        route = self.mesh_routes.get(target_device_id) or self.discover_route(target_device_id)
        if not route:
            return False
        
        print(f"Sending message via mesh: {' -> '.join(route)}")
        return True


@dataclass
class LoRaGateway:
    """LoRa/LoRaWAN gateway"""
    gateway_id: str
    location: Tuple[float, float]
    frequency: float  # MHz
    spreading_factor: int
    coverage_radius_km: float


class LoRaNetwork:
    """Long-range wireless network for device tracking"""
    
    def __init__(self):
        self.gateways: Dict[str, LoRaGateway] = {}
        self.devices: Dict[str, Dict] = {}
    
    def register_gateway(self, gateway_id: str, location: Tuple[float, float], 
                        coverage_radius_km: float = 10.0):
        """Register LoRa gateway"""
        self.gateways[gateway_id] = LoRaGateway(
            gateway_id=gateway_id,
            location=location,
            frequency=915.0,  # MHz (US frequency)
            spreading_factor=7,
            coverage_radius_km=coverage_radius_km
        )
    
    def track_device(self, device_id: str) -> Optional[Tuple[float, float]]:
        """Track device using LoRa triangulation"""
        if device_id not in self.devices:
            return None
        
        device_data = self.devices[device_id]
        
        # Get receiving gateways with RSSI
        receiving_gateways = device_data.get("gateways", [])
        if len(receiving_gateways) < 3:
            # Need at least 3 for triangulation
            return None
        
        # Triangulate position
        return self._triangulate(receiving_gateways)
    
    def _triangulate(self, gateway_data: List[Dict]) -> Tuple[float, float]:
        """Triangulate device position from multiple gateways"""
        # Simplified triangulation using weighted average
        total_weight = 0
        weighted_lat = 0
        weighted_lon = 0
        
        for gw_data in gateway_data:
            gateway = self.gateways.get(gw_data["gateway_id"])
            if not gateway:
                continue
            
            rssi = gw_data["rssi"]
            # Convert RSSI to weight (stronger signal = higher weight)
            weight = 10 ** (rssi / 20.0)
            
            weighted_lat += gateway.location[0] * weight
            weighted_lon += gateway.location[1] * weight
            total_weight += weight
        
        if total_weight == 0:
            return (0, 0)
        
        return (weighted_lat / total_weight, weighted_lon / total_weight)
    
    def receive_uplink(self, device_id: str, gateway_id: str, rssi: int, payload: Dict):
        """Receive LoRa uplink from device"""
        if device_id not in self.devices:
            self.devices[device_id] = {"gateways": [], "last_seen": 0}
        
        # Update gateway list
        gateways = self.devices[device_id]["gateways"]
        gateways = [g for g in gateways if g["gateway_id"] != gateway_id]
        gateways.append({
            "gateway_id": gateway_id,
            "rssi": rssi,
            "timestamp": time.time()
        })
        
        self.devices[device_id]["gateways"] = gateways
        self.devices[device_id]["last_seen"] = time.time()
        self.devices[device_id]["payload"] = payload


class UWBTracker:
    """Ultra-Wideband (UWB) precision tracking"""
    
    def __init__(self):
        self.anchors: Dict[str, Tuple[float, float, float]] = {}  # anchor_id -> (x, y, z)
        self.tags: Dict[str, Dict] = {}
    
    def register_anchor(self, anchor_id: str, position: Tuple[float, float, float]):
        """Register UWB anchor (fixed position)"""
        self.anchors[anchor_id] = position
    
    def calculate_position(self, tag_id: str, ranges: Dict[str, float]) -> Optional[Tuple[float, float, float]]:
        """Calculate 3D position using UWB ranging (Time of Flight)"""
        if len(ranges) < 4:
            # Need at least 4 anchors for 3D position
            return None
        
        # Multilateration using least squares
        # Simplified version - in production use proper multilateration algorithm
        
        anchor_positions = []
        measured_ranges = []
        
        for anchor_id, range_m in ranges.items():
            if anchor_id in self.anchors:
                anchor_positions.append(self.anchors[anchor_id])
                measured_ranges.append(range_m)
        
        if len(anchor_positions) < 4:
            return None
        
        # Simple centroid estimation (mock - real UWB uses proper multilateration)
        x = sum(p[0] for p in anchor_positions) / len(anchor_positions)
        y = sum(p[1] for p in anchor_positions) / len(anchor_positions)
        z = sum(p[2] for p in anchor_positions) / len(anchor_positions)
        
        self.tags[tag_id] = {
            "position": (x, y, z),
            "accuracy_cm": 10.0,  # UWB typical accuracy ~10cm
            "timestamp": time.time()
        }
        
        return (x, y, z)
    
    def get_precision_location(self, tag_id: str) -> Optional[Dict]:
        """Get high-precision UWB location"""
        return self.tags.get(tag_id)


class ComputerVisionLocalizer:
    """Computer vision-based indoor localization"""
    
    def __init__(self):
        self.visual_features: Dict[str, List] = {}  # location_id -> feature descriptors
        self.location_database: Dict[str, Dict] = {}
    
    def index_location(self, location_id: str, image_features: List, 
                      coordinates: Tuple[float, float], floor: int):
        """Index location with visual features"""
        self.visual_features[location_id] = image_features
        self.location_database[location_id] = {
            "coordinates": coordinates,
            "floor": floor,
            "indexed_at": time.time()
        }
    
    def localize_from_image(self, image_features: List) -> Optional[Dict]:
        """Localize device from camera image features"""
        if not self.visual_features:
            return None
        
        # Find best match using feature similarity
        best_match_id = None
        best_similarity = 0
        
        for location_id, stored_features in self.visual_features.items():
            similarity = self._calculate_similarity(image_features, stored_features)
            if similarity > best_similarity:
                best_similarity = similarity
                best_match_id = location_id
        
        if best_similarity < 0.7:  # Confidence threshold
            return None
        
        location = self.location_database.get(best_match_id)
        if not location:
            return None
        
        return {
            "location_id": best_match_id,
            "coordinates": location["coordinates"],
            "floor": location["floor"],
            "confidence": best_similarity,
            "method": "visual_slam"
        }
    
    def _calculate_similarity(self, features1: List, features2: List) -> float:
        """Calculate feature similarity (mock)"""
        # In production: use SIFT, ORB, or deep learning features
        # and compute cosine similarity or Hamming distance
        return 0.85  # Mock similarity
    
    def ar_navigation(self, current_location: Dict, target_location: Dict) -> Dict:
        """Generate AR navigation instructions"""
        # In production: generate AR overlay waypoints
        return {
            "instructions": [
                {"type": "arrow", "direction": "forward", "distance_m": 5},
                {"type": "turn", "direction": "right", "angle": 90},
                {"type": "arrow", "direction": "forward", "distance_m": 3}
            ],
            "estimated_time_seconds": 45
        }


# Global instances
_ble_mesh = None
_lora_network = None
_uwb_tracker = None
_cv_localizer = None

def get_ble_mesh() -> BLEMeshNetwork:
    global _ble_mesh
    if _ble_mesh is None:
        _ble_mesh = BLEMeshNetwork()
    return _ble_mesh

def get_lora_network() -> LoRaNetwork:
    global _lora_network
    if _lora_network is None:
        _lora_network = LoRaNetwork()
    return _lora_network

def get_uwb_tracker() -> UWBTracker:
    global _uwb_tracker
    if _uwb_tracker is None:
        _uwb_tracker = UWBTracker()
    return _uwb_tracker

def get_cv_localizer() -> ComputerVisionLocalizer:
    global _cv_localizer
    if _cv_localizer is None:
        _cv_localizer = ComputerVisionLocalizer()
    return _cv_localizer
