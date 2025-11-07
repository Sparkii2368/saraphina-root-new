"""
Digital Twin Simulation & RL Training Environment.
Simulates device movement, tests recovery strategies, and trains RL agents.
"""
import random
import numpy as np
import time
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json


class LocationType(Enum):
    HOME = "home"
    WORK = "work"
    TRANSIT = "transit"
    PUBLIC = "public"
    LOST = "lost"


@dataclass
class SimulatedDevice:
    """Simulated device with movement patterns"""
    device_id: str
    location: Tuple[float, float]  # (lat, lon)
    location_type: LocationType
    battery_level: float = 100.0
    is_powered: bool = True
    wifi_aps: List[str] = field(default_factory=list)
    ble_beacons: List[str] = field(default_factory=list)
    gps_accuracy: float = 10.0
    last_seen: float = field(default_factory=time.time)
    movement_pattern: str = "stationary"  # stationary, walking, driving


class DeviceSimulator:
    """Simulates device movement and sensor data"""
    
    def __init__(self, seed: Optional[int] = None):
        if seed:
            random.seed(seed)
            np.random.seed(seed)
        
        self.devices: Dict[str, SimulatedDevice] = {}
        self.time_step = 0
        self.location_zones = self._generate_zones()
    
    def _generate_zones(self) -> Dict[str, Dict]:
        """Generate common location zones"""
        return {
            "home": {"center": (37.7749, -122.4194), "radius_km": 0.5},
            "work": {"center": (37.7849, -122.4094), "radius_km": 0.3},
            "downtown": {"center": (37.7899, -122.3950), "radius_km": 1.0},
        }
    
    def add_device(self, device_id: str, initial_location: Tuple[float, float], 
                   location_type: LocationType = LocationType.HOME):
        """Add device to simulation"""
        self.devices[device_id] = SimulatedDevice(
            device_id=device_id,
            location=initial_location,
            location_type=location_type,
            wifi_aps=self._generate_wifi_aps(initial_location),
            ble_beacons=self._generate_ble_beacons(initial_location)
        )
    
    def _generate_wifi_aps(self, location: Tuple[float, float]) -> List[str]:
        """Generate nearby WiFi APs"""
        num_aps = random.randint(2, 8)
        return [f"AP-{random.randint(1000, 9999)}" for _ in range(num_aps)]
    
    def _generate_ble_beacons(self, location: Tuple[float, float]) -> List[str]:
        """Generate nearby BLE beacons"""
        num_beacons = random.randint(0, 5)
        return [f"BLE-{random.randint(1000, 9999)}" for _ in range(num_beacons)]
    
    def step(self, device_id: str, duration_minutes: float = 1.0):
        """Simulate one time step"""
        if device_id not in self.devices:
            return
        
        device = self.devices[device_id]
        self.time_step += 1
        
        # Update battery
        drain_rate = 0.1 if device.is_powered else 0.5
        device.battery_level = max(0, device.battery_level - drain_rate * duration_minutes)
        
        # Move device based on pattern
        if device.movement_pattern == "walking":
            device.location = self._walk_step(device.location)
            device.gps_accuracy = random.uniform(5, 15)
        elif device.movement_pattern == "driving":
            device.location = self._drive_step(device.location)
            device.gps_accuracy = random.uniform(10, 50)
        else:  # stationary
            device.gps_accuracy = random.uniform(3, 10)
        
        # Update sensors
        device.wifi_aps = self._generate_wifi_aps(device.location)
        device.ble_beacons = self._generate_ble_beacons(device.location)
        device.last_seen = time.time()
    
    def _walk_step(self, location: Tuple[float, float]) -> Tuple[float, float]:
        """Simulate walking movement (~5 km/h)"""
        lat, lon = location
        # ~0.001 degrees = ~100m
        lat += random.uniform(-0.001, 0.001)
        lon += random.uniform(-0.001, 0.001)
        return (lat, lon)
    
    def _drive_step(self, location: Tuple[float, float]) -> Tuple[float, float]:
        """Simulate driving movement (~50 km/h)"""
        lat, lon = location
        lat += random.uniform(-0.01, 0.01)
        lon += random.uniform(-0.01, 0.01)
        return (lat, lon)
    
    def simulate_loss(self, device_id: str, loss_scenario: str = "random"):
        """Simulate device loss"""
        if device_id not in self.devices:
            return
        
        device = self.devices[device_id]
        
        if loss_scenario == "battery_dead":
            device.battery_level = 0
            device.is_powered = False
        elif loss_scenario == "dropped":
            device.movement_pattern = "stationary"
            device.location_type = LocationType.LOST
        elif loss_scenario == "stolen":
            device.movement_pattern = "driving"
            device.location_type = LocationType.TRANSIT
        else:  # random
            device.location_type = LocationType.LOST
    
    def get_telemetry(self, device_id: str) -> Optional[Dict]:
        """Get current device telemetry"""
        device = self.devices.get(device_id)
        if not device:
            return None
        
        return {
            "device_id": device_id,
            "location": device.location,
            "battery_level": device.battery_level,
            "is_powered": device.is_powered,
            "wifi_aps": device.wifi_aps,
            "ble_beacons": device.ble_beacons,
            "gps_accuracy": device.gps_accuracy,
            "last_seen": device.last_seen,
            "location_type": device.location_type.value
        }


class RecoveryEnvironment:
    """RL Environment for recovery strategy training"""
    
    def __init__(self, simulator: DeviceSimulator):
        self.simulator = simulator
        self.current_device = None
        self.steps_taken = 0
        self.max_steps = 20
        self.recovery_methods = ["gps", "wifi", "ble", "last_known", "sound_alert"]
    
    def reset(self, device_id: str) -> Dict:
        """Reset environment for new episode"""
        self.current_device = device_id
        self.steps_taken = 0
        
        # Simulate random loss
        self.simulator.simulate_loss(device_id, random.choice(["dropped", "battery_dead", "random"]))
        
        return self._get_state()
    
    def _get_state(self) -> Dict:
        """Get current state representation"""
        telemetry = self.simulator.get_telemetry(self.current_device)
        if not telemetry:
            return {}
        
        device = self.simulator.devices[self.current_device]
        
        # State features for RL agent
        state = {
            "battery_level": device.battery_level / 100.0,
            "is_powered": 1.0 if device.is_powered else 0.0,
            "num_wifi_aps": len(device.wifi_aps) / 10.0,
            "num_ble_beacons": len(device.ble_beacons) / 10.0,
            "gps_accuracy": device.gps_accuracy / 100.0,
            "time_since_seen": min((time.time() - device.last_seen) / 3600.0, 1.0),
            "steps_taken": self.steps_taken / self.max_steps
        }
        
        return state
    
    def step(self, action: int) -> Tuple[Dict, float, bool, Dict]:
        """Execute action and return (state, reward, done, info)"""
        self.steps_taken += 1
        
        method = self.recovery_methods[action]
        device = self.simulator.devices[self.current_device]
        
        # Simulate recovery attempt
        success_prob = self._calculate_success_probability(method, device)
        success = random.random() < success_prob
        
        # Calculate reward
        reward = 0.0
        if success:
            reward = 10.0 - (self.steps_taken * 0.5)  # Faster = better
        else:
            reward = -1.0  # Penalty for failed attempt
        
        # Check if done
        done = success or self.steps_taken >= self.max_steps
        
        # Advance simulation
        self.simulator.step(self.current_device, duration_minutes=5)
        
        info = {
            "method": method,
            "success": success,
            "success_prob": success_prob
        }
        
        return self._get_state(), reward, done, info
    
    def _calculate_success_probability(self, method: str, device: SimulatedDevice) -> float:
        """Calculate probability of success for recovery method"""
        if method == "gps":
            if device.battery_level > 20 and device.is_powered:
                return 0.8 - (device.gps_accuracy / 100.0)
            return 0.1
        
        elif method == "wifi":
            if len(device.wifi_aps) > 2:
                return 0.6
            return 0.2
        
        elif method == "ble":
            if len(device.ble_beacons) > 0:
                return 0.7
            return 0.1
        
        elif method == "last_known":
            if device.movement_pattern == "stationary":
                return 0.5
            return 0.2
        
        elif method == "sound_alert":
            if device.battery_level > 5:
                return 0.4
            return 0.0
        
        return 0.3


class ABTestFramework:
    """A/B testing for recovery strategies"""
    
    def __init__(self):
        self.experiments: Dict[str, Dict] = {}
        self.results: Dict[str, List[Dict]] = {}
    
    def create_experiment(self, experiment_id: str, variants: List[str], description: str):
        """Create new A/B test experiment"""
        self.experiments[experiment_id] = {
            "variants": variants,
            "description": description,
            "created_at": time.time(),
            "active": True
        }
        for variant in variants:
            self.results[f"{experiment_id}:{variant}"] = []
    
    def assign_variant(self, experiment_id: str, user_id: str) -> str:
        """Assign user to variant"""
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        variants = self.experiments[experiment_id]["variants"]
        # Deterministic assignment based on user_id hash
        hash_val = hash(user_id) % len(variants)
        return variants[hash_val]
    
    def record_result(self, experiment_id: str, variant: str, success: bool, metrics: Dict):
        """Record experiment result"""
        key = f"{experiment_id}:{variant}"
        if key not in self.results:
            return
        
        self.results[key].append({
            "success": success,
            "metrics": metrics,
            "timestamp": time.time()
        })
    
    def analyze_experiment(self, experiment_id: str) -> Dict:
        """Analyze experiment results"""
        if experiment_id not in self.experiments:
            return {}
        
        variants = self.experiments[experiment_id]["variants"]
        analysis = {}
        
        for variant in variants:
            key = f"{experiment_id}:{variant}"
            results = self.results.get(key, [])
            
            if not results:
                continue
            
            success_rate = sum(r["success"] for r in results) / len(results)
            avg_time = np.mean([r["metrics"].get("time_to_recovery", 0) for r in results])
            
            analysis[variant] = {
                "n_samples": len(results),
                "success_rate": success_rate,
                "avg_time_to_recovery": avg_time
            }
        
        return analysis


class SyntheticDataGenerator:
    """Generate synthetic device data for testing"""
    
    @staticmethod
    def generate_location_history(device_id: str, num_days: int = 30) -> List[Dict]:
        """Generate synthetic location history"""
        history = []
        base_time = time.time() - (num_days * 86400)
        
        home = (37.7749, -122.4194)
        work = (37.7849, -122.4094)
        
        for day in range(num_days):
            day_start = base_time + (day * 86400)
            
            # Morning at home
            for hour in range(0, 8):
                history.append({
                    "device_id": device_id,
                    "timestamp": day_start + (hour * 3600),
                    "location": home,
                    "location_type": "home"
                })
            
            # Transit to work
            history.append({
                "device_id": device_id,
                "timestamp": day_start + (8 * 3600),
                "location": ((home[0] + work[0]) / 2, (home[1] + work[1]) / 2),
                "location_type": "transit"
            })
            
            # At work
            for hour in range(9, 17):
                history.append({
                    "device_id": device_id,
                    "timestamp": day_start + (hour * 3600),
                    "location": work,
                    "location_type": "work"
                })
            
            # Transit home
            history.append({
                "device_id": device_id,
                "timestamp": day_start + (17 * 3600),
                "location": ((home[0] + work[0]) / 2, (home[1] + work[1]) / 2),
                "location_type": "transit"
            })
            
            # Evening at home
            for hour in range(18, 24):
                history.append({
                    "device_id": device_id,
                    "timestamp": day_start + (hour * 3600),
                    "location": home,
                    "location_type": "home"
                })
        
        return history
    
    @staticmethod
    def generate_recovery_scenarios(num_scenarios: int = 100) -> List[Dict]:
        """Generate synthetic recovery scenarios"""
        scenarios = []
        
        for i in range(num_scenarios):
            scenario = {
                "scenario_id": f"scenario-{i}",
                "loss_type": random.choice(["dropped", "stolen", "battery_dead", "forgotten"]),
                "location_type": random.choice(["home", "work", "public", "transit"]),
                "battery_level": random.uniform(0, 100),
                "time_since_loss": random.uniform(0, 24),  # hours
                "successful_method": random.choice(["gps", "wifi", "ble", "sound", "manual"])
            }
            scenarios.append(scenario)
        
        return scenarios
