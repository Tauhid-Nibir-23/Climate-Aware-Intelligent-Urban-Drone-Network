"""
Automated unit tests for simulation performance metrics:
average delivery time, total energy consumption, delivery success rate,
failed delivery count, and drone utilization.
"""
import pytest
from src.models import Drone, DeliveryRequest
from src.simulation import DroneDeliverySimulation


def test_metrics_calculations_normal_delivery(
    network, drone_fleet: list[Drone], bapa_dispatcher, temperate_weather
):
    """
    Verifies exact mathematical accuracy of:
    - Average delivery turnaround time
    - Total energy consumption
    - Delivery success rate & mission success rate
    - Failed delivery count (0 in normal scenario)
    - Drone utilization percentage
    """
    requests = [
        DeliveryRequest("REQ-M1", "LOC-PSTU-CSE", arrival_time_min=0.0, package_weight_kg=1.0),
        DeliveryRequest("REQ-M2", "LOC-PSTU-MED", arrival_time_min=2.0, package_weight_kg=1.5),
    ]

    sim = DroneDeliverySimulation(
        network=network,
        drones=drone_fleet,
        requests=requests,
        dispatcher=bapa_dispatcher,
        weather=temperate_weather,
    )
    sim.run(max_duration_min=60.0)
    metrics = sim.get_summary_metrics()

    assert metrics["total_orders"] == 2
    assert metrics["delivered_orders"] == 2
    assert metrics["failed_orders"] == 0
    assert metrics["completed_missions"] == 2
    assert metrics["failed_missions"] == 0
    assert metrics["return_leg_failures"] == 0
    assert metrics["failed_drones"] == 0
    assert metrics["success_rate_pct"] == 100.0
    assert metrics["mission_success_rate_pct"] == 100.0

    # Verify average delivery time against individual order turnaround times
    expected_turnarounds = [r.delivery_time_min - r.arrival_time_min for r in sim.completed_orders]
    expected_avg_time = round(sum(expected_turnarounds) / len(expected_turnarounds), 2)
    assert metrics["avg_delivery_time_min"] == expected_avg_time
    assert metrics["avg_delivery_time_min"] > 0.0

    # Verify total energy consumption matches sum of fleet energy
    expected_energy = round(sum(d.total_energy_consumed_wh for d in drone_fleet), 2)
    assert metrics["total_energy_consumed_wh"] == expected_energy
    assert metrics["total_energy_consumed_wh"] > 0.0

    # Verify drone utilization matches (total_flight_time / (N_drones * sim_horizon)) * 100
    total_flight_min = sum(d.total_flight_time_min for d in drone_fleet)
    expected_util = round((total_flight_min / (len(drone_fleet) * 60.0)) * 100.0, 2)
    assert metrics["drone_utilization_pct"] == expected_util
    assert 0.0 < metrics["drone_utilization_pct"] <= 100.0


def test_metrics_failed_delivery_and_mutual_exclusivity(
    network, default_specs, fcfs_dispatcher, extreme_weather
):
    """
    Verifies metric denominators and ensures no delivery request is ever counted twice
    across mixed outcomes (1 full success, 1 return-leg failure, 1 outbound failure).
    """
    d1 = Drone("DRONE-01", default_specs)
    d1.battery.current_soc = 1.00  # Will succeed completely on short trip

    d2 = Drone("DRONE-02", default_specs)
    d2.battery.current_soc = 0.45  # Will deliver to LOC-ANGARIA but fail on return leg

    d3 = Drone("DRONE-03", default_specs)
    d3.battery.current_soc = 0.15  # Will fail on outbound leg to LOC-ANGARIA

    requests = [
        DeliveryRequest("REQ-MIX-1", "LOC-PSTU-CSE", arrival_time_min=0.0, package_weight_kg=1.0),
        DeliveryRequest("REQ-MIX-2", "LOC-ANGARIA", arrival_time_min=0.0, package_weight_kg=2.5),
        DeliveryRequest("REQ-MIX-3", "LOC-ANGARIA", arrival_time_min=0.0, package_weight_kg=2.5),
    ]

    sim = DroneDeliverySimulation(
        network=network,
        drones=[d1, d2, d3],
        requests=requests,
        dispatcher=fcfs_dispatcher,
        weather=extreme_weather,
    )
    sim.run(max_duration_min=60.0)
    metrics = sim.get_summary_metrics()

    # Check mutual exclusivity between completed_orders and failed_orders
    completed_ids = {r.request_id for r in sim.completed_orders}
    failed_ids = {r.request_id for r in sim.failed_orders}
    assert completed_ids.isdisjoint(failed_ids)
    assert len(completed_ids) + len(failed_ids) == 3

    # REQ-MIX-1 and REQ-MIX-2 delivered packages; REQ-MIX-3 failed outbound
    assert metrics["total_orders"] == 3
    assert metrics["delivered_orders"] == 2
    assert metrics["failed_orders"] == 1
    assert metrics["success_rate_pct"] == pytest.approx(66.7, abs=0.1)

    # Mission level: only REQ-MIX-1 completed full round-trip; REQ-MIX-2 and REQ-MIX-3 failed missions
    assert metrics["completed_missions"] == 1
    assert metrics["failed_missions"] == 2
    assert metrics["return_leg_failures"] == 1
    assert metrics["failed_drones"] == 2
    assert metrics["mission_success_rate_pct"] == pytest.approx(33.3, abs=0.1)


def test_metrics_empty_requests_zero_division_safety(
    network, single_drone: Drone, bapa_dispatcher, temperate_weather
):
    """Verifies get_summary_metrics handles 0 orders and 0 elapsed time without ZeroDivisionError."""
    sim = DroneDeliverySimulation(
        network=network,
        drones=[single_drone],
        requests=[],
        dispatcher=bapa_dispatcher,
        weather=temperate_weather,
    )
    metrics = sim.get_summary_metrics()
    assert metrics["total_orders"] == 0
    assert metrics["delivered_orders"] == 0
    assert metrics["failed_orders"] == 0
    assert metrics["success_rate_pct"] == 0.0
    assert metrics["mission_success_rate_pct"] == 0.0
    assert metrics["avg_delivery_time_min"] == 0.0
    assert metrics["drone_utilization_pct"] == 0.0

