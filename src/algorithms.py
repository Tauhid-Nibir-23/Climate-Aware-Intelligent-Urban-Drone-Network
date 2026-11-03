"""
Dispatching and Scheduling Algorithms for Multi-Drone Delivery.
Compares Baseline FCFS with Proposed Battery-Aware Assignment.
"""
from __future__ import annotations
from typing import List, Optional, Tuple
from src.models import Drone, DeliveryRequest, DroneStatus
from src.network import DumkiNetwork
from src.config import WeatherScenario

class BaseDispatcher:
    """Abstract base class for drone dispatch policies."""
    def __init__(self, name: str):
        self.name = name

    def select_drone_for_request(
        self,
        request: DeliveryRequest,
        fleet: List[Drone],
        network: DumkiNetwork,
        weather: WeatherScenario
    ) -> Optional[Drone]:
        raise NotImplementedError

class FCFSDispatcher(BaseDispatcher):
    """
    Baseline First-Come First-Served + Greedy Nearest Idle Drone.
    Does NOT calculate round-trip energy feasibility before dispatch.
    """
    def __init__(self):
        super().__init__("Baseline (FCFS + Greedy)")

    def select_drone_for_request(
        self,
        request: DeliveryRequest,
        fleet: List[Drone],
        network: DumkiNetwork,
        weather: WeatherScenario
    ) -> Optional[Drone]:
        depot_id = network.get_depot_id()
        # Find idle drones currently at depot that satisfy payload and positive battery operational constraints
        available_drones = [
            d for d in fleet
            if d.is_available()
            and d.current_node == depot_id
            and d.battery.current_soc > 0.0
            and 0.0 <= request.package_weight_kg <= d.specs.max_payload_kg
        ]
        if not available_drones:
            return None
        # Naively pick the first idle drone
        return available_drones[0]

class BatteryAwareDispatcher(BaseDispatcher):
    """
    Proposed Battery-Aware & Payload-Constrained Dispatcher (BAPA).
    Computes required round-trip energy (outbound with package, inbound empty)
    under the ambient weather scenario, enforcing the safety reserve constraint.
    """
    def __init__(self):
        super().__init__("Proposed (Battery-Aware)")

    def select_drone_for_request(
        self,
        request: DeliveryRequest,
        fleet: List[Drone],
        network: DumkiNetwork,
        weather: WeatherScenario
    ) -> Optional[Drone]:
        depot_id = network.get_depot_id()
        dist_km = network.get_distance_km(depot_id, request.destination_node)
        
        available_drones = [
            d for d in fleet
            if d.is_available()
            and d.current_node == depot_id
            and 0.0 <= request.package_weight_kg <= d.specs.max_payload_kg
        ]
        if not available_drones:
            return None

        feasible_candidates: List[Tuple[Drone, float]] = []

        for drone in available_drones:
            # 1. Outbound leg energy (loaded with package)
            outbound_wh = drone.battery.calculate_trip_energy_wh(
                distance_km=dist_km,
                speed_mps=drone.specs.cruising_speed_mps,
                payload_kg=request.package_weight_kg,
                base_power_w=drone.specs.base_power_w,
                payload_power_coeff=drone.specs.payload_power_coeff_w_per_kg,
                climate_multiplier=weather.climate_multiplier,
                maneuver_time_s=drone.specs.takeoff_landing_time_s
            )

            # 2. Inbound return leg energy (empty drone)
            return_wh = drone.battery.calculate_trip_energy_wh(
                distance_km=dist_km,
                speed_mps=drone.specs.cruising_speed_mps,
                payload_kg=0.0,
                base_power_w=drone.specs.base_power_w,
                payload_power_coeff=drone.specs.payload_power_coeff_w_per_kg,
                climate_multiplier=weather.climate_multiplier,
                maneuver_time_s=drone.specs.takeoff_landing_time_s
            )

            total_trip_wh = outbound_wh + return_wh
            required_soc_fraction = total_trip_wh / drone.specs.battery_capacity_wh
            projected_final_soc = drone.battery.current_soc - required_soc_fraction

            # Check hard safety reserve constraint
            if projected_final_soc >= drone.specs.min_reserve_soc:
                feasible_candidates.append((drone, projected_final_soc))

        if not feasible_candidates:
            # No drone can safely perform this trip right now; keep order safely in queue
            return None

        # Best-fit selection: pick the drone that leaves the lowest acceptable surplus above reserve,
        # preserving the highest-capacity drones for longer/heavier upcoming missions.
        feasible_candidates.sort(key=lambda x: x[1])
        return feasible_candidates[0][0]

