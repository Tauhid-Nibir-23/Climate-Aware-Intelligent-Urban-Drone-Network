"""
Data models and entities for the Multi-Drone Simulation.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from src.config import DroneSpecs

class DroneStatus(str, Enum):
    IDLE = "IDLE"
    OUTBOUND_DELIVERY = "OUTBOUND_DELIVERY"
    RETURNING = "RETURNING"
    WAITING_FOR_CHARGER = "WAITING_FOR_CHARGER"
    CHARGING = "CHARGING"
    FAILED_OUT_OF_BATTERY = "FAILED_OUT_OF_BATTERY"

@dataclass
class DeliveryRequest:
    """Represents a customer order for medical/essential supplies."""
    request_id: str
    destination_node: str
    arrival_time_min: float
    package_weight_kg: float
    urgency_deadline_min: float = 60.0
    status: str = "PENDING"  # PENDING, IN_TRANSIT, DELIVERED, INFEASIBLE, FAILED
    delivery_time_min: Optional[float] = None
    assigned_drone_id: Optional[str] = None
    dispatch_time_min: Optional[float] = None
    return_time_min: Optional[float] = None
    failure_time_min: Optional[float] = None
    mission_status: str = "PENDING"  # PENDING, OUTBOUND, RETURNING, COMPLETED, OUTBOUND_FAILED, RETURN_FAILED

@dataclass
class Battery:
    """Models LiPo battery state, discharge under payload, and linear recharging."""
    capacity_wh: float
    current_soc: float = 1.0  # State of Charge [0.0, 1.0]

    def __post_init__(self):
        if self.capacity_wh <= 0:
            raise ValueError("Battery capacity_wh must be positive.")
        self.current_soc = max(0.0, min(1.0, float(self.current_soc)))

    @property
    def remaining_energy_wh(self) -> float:
        return self.capacity_wh * self.current_soc

    def calculate_trip_energy_wh(
        self,
        distance_km: float,
        speed_mps: float,
        payload_kg: float,
        base_power_w: float,
        payload_power_coeff: float,
        climate_multiplier: float = 1.0,
        maneuver_time_s: float = 60.0
    ) -> float:
        """
        Calculates required electrical energy (Wh) for a single flight leg.
        Energy = Power (W) * Time (hours) * Climate Multiplier.
        """
        if distance_km < 0:
            raise ValueError("Distance cannot be negative.")
        if speed_mps <= 0:
            raise ValueError("Cruising speed must be positive.")
        if payload_kg < 0:
            raise ValueError("Payload weight cannot be negative.")
        if climate_multiplier <= 0:
            raise ValueError("Climate multiplier must be positive.")
        if maneuver_time_s < 0:
            raise ValueError("Maneuver time cannot be negative.")

        flight_time_s = (distance_km * 1000.0 / speed_mps) + maneuver_time_s
        flight_time_hr = flight_time_s / 3600.0
        total_power_w = base_power_w + (payload_power_coeff * payload_kg)
        trip_energy_wh = total_power_w * flight_time_hr * climate_multiplier
        return trip_energy_wh

    def discharge(self, energy_wh: float) -> bool:
        """
        Decrements battery state of charge. Returns False if depleted to 0.
        """
        if energy_wh < 0:
            raise ValueError("Discharge energy_wh cannot be negative.")
        soc_delta = energy_wh / self.capacity_wh
        self.current_soc = max(0.0, self.current_soc - soc_delta)
        return self.current_soc > 0.0

    def recharge(self, energy_wh: float) -> None:
        """Restores battery state of charge up to 1.0."""
        if energy_wh < 0:
            raise ValueError("Recharge energy_wh cannot be negative.")
        soc_delta = energy_wh / self.capacity_wh
        self.current_soc = min(1.0, self.current_soc + soc_delta)

@dataclass
class Drone:
    """Represents an autonomous multi-rotor delivery drone entity."""
    drone_id: str
    specs: DroneSpecs = field(default_factory=DroneSpecs)
    current_node: str = "DEPOT-PSTU"
    status: DroneStatus = DroneStatus.IDLE
    battery: Battery = field(init=False)
    
    # Cumulative operational telemetry
    total_deliveries: int = 0
    completed_missions: int = 0
    failed_missions: int = 0
    total_distance_km: float = 0.0
    total_energy_consumed_wh: float = 0.0
    total_flight_time_min: float = 0.0
    total_charging_wait_min: float = 0.0
    current_request_id: Optional[str] = None
    failure_time_min: Optional[float] = None

    def __post_init__(self):
        self.battery = Battery(capacity_wh=self.specs.battery_capacity_wh, current_soc=1.0)

    def is_available(self) -> bool:
        return self.status == DroneStatus.IDLE and self.current_request_id is None

