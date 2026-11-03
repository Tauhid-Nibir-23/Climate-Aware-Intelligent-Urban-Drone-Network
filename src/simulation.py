"""
Core Discrete-Event Simulation (DES) Engine using SimPy.
Simulates fleet flight dynamics, battery drain, payload drop-offs, and charging bay queues.
"""
from __future__ import annotations
from typing import List, Dict, Any
import pandas as pd
import simpy

from src.models import Drone, DeliveryRequest, DroneStatus
from src.network import DumkiNetwork
from src.config import WeatherScenario
from src.algorithms import BaseDispatcher

class DroneDeliverySimulation:
    def __init__(
        self,
        network: DumkiNetwork,
        drones: List[Drone],
        requests: List[DeliveryRequest],
        dispatcher: BaseDispatcher,
        weather: WeatherScenario,
        num_charging_bays: int = 2,
        recharge_threshold_soc: float = 0.50
    ):
        self.network = network
        self.drones = drones
        self.requests = requests
        self.dispatcher = dispatcher
        self.weather = weather
        self.num_charging_bays = num_charging_bays
        self.recharge_threshold_soc = recharge_threshold_soc

        self.env = simpy.Environment()
        self.charging_station = simpy.Resource(self.env, capacity=self.num_charging_bays)
        self.events_log: List[Dict[str, Any]] = []

        # Order queues
        self.pending_orders: List[DeliveryRequest] = []
        self.completed_orders: List[DeliveryRequest] = []
        self.failed_orders: List[DeliveryRequest] = []

    def log_event(self, event_type: str, drone_id: str, details: str, soc: float = 1.0):
        self.events_log.append({
            "simulation_time_min": round(self.env.now, 2),
            "event_type": event_type,
            "drone_id": drone_id,
            "soc": round(soc, 3),
            "details": details
        })

    def run(self, max_duration_min: float = 360.0) -> pd.DataFrame:
        """Starts all SimPy processes and runs the event calendar."""
        self.env.process(self._order_arrival_process())
        self.env.process(self._dispatch_scheduler_process())
        self.env.run(until=max_duration_min)
        return self.get_event_log_df()

    def _order_arrival_process(self):
        """Generates order arrivals over simulation time."""
        for req in sorted(self.requests, key=lambda r: r.arrival_time_min):
            wait_time = req.arrival_time_min - self.env.now
            if wait_time > 0:
                yield self.env.timeout(wait_time)
            self.pending_orders.append(req)
            self.log_event("ORDER_ARRIVED", "SYSTEM", f"Order {req.request_id} arrived for {req.destination_node} ({req.package_weight_kg}kg)")

    def _dispatch_scheduler_process(self):
        """Continuously inspects pending orders and attempts to dispatch idle drones."""
        while True:
            if self.pending_orders:
                for req in list(self.pending_orders):
                    selected_drone = self.dispatcher.select_drone_for_request(
                        req, self.drones, self.network, self.weather
                    )
                    if selected_drone:
                        self.pending_orders.remove(req)
                        req.assigned_drone_id = selected_drone.drone_id
                        req.status = "IN_TRANSIT"
                        self.env.process(self._drone_mission_process(selected_drone, req))
            yield self.env.timeout(1.0)  # Check dispatch queue every simulated minute

    def _drone_mission_process(self, drone: Drone, request: DeliveryRequest):
        """Models the complete delivery mission: Outbound -> Drop-off -> Inbound -> Recharging."""
        depot_id = self.network.get_depot_id()
        dest_id = request.destination_node
        dist_km = self.network.get_distance_km(depot_id, dest_id)
        
        # Flight leg timing
        leg_time_min = ((dist_km * 1000.0 / drone.specs.cruising_speed_mps) + drone.specs.takeoff_landing_time_s) / 60.0

        # --- OUTBOUND LEG ---
        drone.status = DroneStatus.OUTBOUND_DELIVERY
        outbound_wh = drone.battery.calculate_trip_energy_wh(
            dist_km, drone.specs.cruising_speed_mps, request.package_weight_kg,
            drone.specs.base_power_w, drone.specs.payload_power_coeff_w_per_kg,
            self.weather.climate_multiplier, drone.specs.takeoff_landing_time_s
        )

        self.log_event("MISSION_DISPATCH", drone.drone_id, f"Departing to {dest_id} with {request.request_id}", drone.battery.current_soc)
        yield self.env.timeout(leg_time_min)

        survived = drone.battery.discharge(outbound_wh)
        drone.total_energy_consumed_wh += outbound_wh
        drone.total_distance_km += dist_km
        drone.total_flight_time_min += leg_time_min

        if not survived:
            # Catastrophic failure: battery drained to 0 in flight!
            drone.status = DroneStatus.FAILED_OUT_OF_BATTERY
            request.status = "FAILED"
            self.failed_orders.append(request)
            self.log_event("MISSION_FAILED", drone.drone_id, f"Battery depleted mid-flight to {dest_id}!", 0.0)
            return

        # Delivery successful at destination
        request.status = "DELIVERED"
        request.delivery_time_min = round(self.env.now, 2)
        self.completed_orders.append(request)
        drone.total_deliveries += 1
        self.log_event("PACKAGE_DELIVERED", drone.drone_id, f"Package {request.request_id} delivered at {dest_id}", drone.battery.current_soc)

        # --- INBOUND LEG (EMPTY RETURN) ---
        drone.status = DroneStatus.RETURNING
        return_wh = drone.battery.calculate_trip_energy_wh(
            dist_km, drone.specs.cruising_speed_mps, 0.0,
            drone.specs.base_power_w, drone.specs.payload_power_coeff_w_per_kg,
            self.weather.climate_multiplier, drone.specs.takeoff_landing_time_s
        )

        yield self.env.timeout(leg_time_min)
        survived = drone.battery.discharge(return_wh)
        drone.total_energy_consumed_wh += return_wh
        drone.total_distance_km += dist_km
        drone.total_flight_time_min += leg_time_min

        if not survived:
            drone.status = DroneStatus.FAILED_OUT_OF_BATTERY
            self.log_event("RETURN_FAILED", drone.drone_id, f"Battery died on return journey to depot!", 0.0)
            return

        self.log_event("RETURNED_TO_DEPOT", drone.drone_id, f"Safely returned to depot with SoC: {drone.battery.current_soc*100:.1f}%", drone.battery.current_soc)

        # --- CHARGING STATION RESOURCE QUEUE ---
        if drone.battery.current_soc < self.recharge_threshold_soc:
            drone.status = DroneStatus.WAITING_FOR_CHARGER
            wait_start = self.env.now
            self.log_event("CHARGING_QUEUE_ENTER", drone.drone_id, "Queuing for depot charging bay", drone.battery.current_soc)

            with self.charging_station.request() as req_bay:
                yield req_bay  # Enqueued until a charging bay is available
                wait_duration = self.env.now - wait_start
                drone.total_charging_wait_min += wait_duration

                drone.status = DroneStatus.CHARGING
                self.log_event("CHARGING_STARTED", drone.drone_id, f"Acquired charging bay after {wait_duration:.1f}min wait", drone.battery.current_soc)

                # Recharge to 100%
                energy_needed_wh = drone.specs.battery_capacity_wh * (1.0 - drone.battery.current_soc)
                charge_time_hr = energy_needed_wh / (drone.specs.recharge_power_w * drone.specs.charging_efficiency)
                charge_time_min = charge_time_hr * 60.0

                yield self.env.timeout(charge_time_min)
                drone.battery.current_soc = 1.0
                self.log_event("CHARGING_COMPLETED", drone.drone_id, "Recharged to 100% capacity", 1.0)

        drone.status = DroneStatus.IDLE
        self.log_event("DRONE_AVAILABLE", drone.drone_id, "Drone back in IDLE status at depot", drone.battery.current_soc)

    def get_event_log_df(self) -> pd.DataFrame:
        return pd.DataFrame(self.events_log)

    def get_summary_metrics(self) -> Dict[str, Any]:
        """Calculates global simulation performance indicators."""
        total_orders = len(self.requests)
        delivered_orders = len(self.completed_orders)
        failed_orders = len(self.failed_orders)
        success_rate = (delivered_orders / total_orders * 100.0) if total_orders > 0 else 0.0

        turnaround_times = [
            (r.delivery_time_min - r.arrival_time_min)
            for r in self.completed_orders
            if r.delivery_time_min is not None
        ]
        avg_turnaround = (sum(turnaround_times) / len(turnaround_times)) if turnaround_times else 0.0
        total_energy = sum(d.total_energy_consumed_wh for d in self.drones)
        total_distance = sum(d.total_distance_km for d in self.drones)
        total_charging_wait = sum(d.total_charging_wait_min for d in self.drones)

        return {
            "algorithm": self.dispatcher.name,
            "weather_scenario": self.weather.name,
            "total_orders": total_orders,
            "delivered_orders": delivered_orders,
            "failed_orders": failed_orders,
            "success_rate_pct": round(success_rate, 1),
            "avg_delivery_time_min": round(avg_turnaround, 2),
            "total_energy_consumed_wh": round(total_energy, 2),
            "total_distance_km": round(total_distance, 2),
            "total_charging_wait_min": round(total_charging_wait, 2),
        }

