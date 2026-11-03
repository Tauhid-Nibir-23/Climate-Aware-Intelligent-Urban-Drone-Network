"""
Automated tests for DroneDeliverySimulation execution, clock progression,
return-leg failure accounting (Bug #2 regression), outbound failure, and seed reproducibility.
"""
import copy
from src.models import Drone, DeliveryRequest, DroneStatus
from src.generator import generate_synthetic_requests
from src.simulation import DroneDeliverySimulation


def test_simulation_clock_advances_and_processes_requests(
    network, drone_fleet: list[Drone], bapa_dispatcher, temperate_weather
):
    """Verifies that SimPy virtual clock advances and processes incoming requests."""
    requests = [
        DeliveryRequest("REQ-CLK-1", "LOC-PSTU-CSE", arrival_time_min=5.0, package_weight_kg=1.0),
        DeliveryRequest("REQ-CLK-2", "LOC-DUMKI-HOSP", arrival_time_min=15.0, package_weight_kg=1.5),
    ]
    sim = DroneDeliverySimulation(
        network=network,
        drones=drone_fleet,
        requests=requests,
        dispatcher=bapa_dispatcher,
        weather=temperate_weather,
    )
    df_events = sim.run(max_duration_min=90.0)

    assert sim.env.now == 90.0
    assert not df_events.empty
    assert len(sim.completed_orders) == 2
    assert len(sim.completed_missions) == 2
    assert len(sim.failed_orders) == 0
    assert len(sim.failed_missions) == 0


def test_bug2_regression_return_leg_failure_accounting(
    network, single_drone: Drone, fcfs_dispatcher, extreme_weather
):
    """
    Regression test for Bug #2 (Return-Leg Failure Accounting):
    Scenario:
    - Drone starts with 45% SoC (81.0 Wh).
    - Dispatched under FCFS to LOC-ANGARIA (5.34 km, 2.5 kg) in Extreme Heatwave (1.40x).
    - Outbound leg consumes ~63.3 Wh (~35.2% SoC), leaving ~9.8% SoC -> Outbound SURVIVES!
    - Package is delivered to the customer at LOC-ANGARIA.
    - Return leg (0 kg payload) requires ~41.2 Wh (~22.9% SoC), which exceeds remaining ~9.8% SoC.
    - Drone depletes battery to 0% on the return journey (RETURN_FAILED).

    Required verified behavior:
    1. Customer delivery completion is recorded once in `completed_orders` (`status == "DELIVERED"`).
    2. Request is NOT double-counted in `failed_orders` (`len(failed_orders) == 0`).
    3. Return-leg failure is tracked separately in `return_failures` and `failed_missions`
       (`mission_status == "RETURN_FAILED"`, `failure_time_min` set).
    4. Full mission is NOT counted in `completed_missions`.
    5. Drone status is permanently `FAILED_OUT_OF_BATTERY` and `failed_drones == 1`.
    """
    single_drone.battery.current_soc = 0.45
    req = DeliveryRequest(
        request_id="REQ-RET-FAIL-01",
        destination_node="LOC-ANGARIA",
        arrival_time_min=0.0,
        package_weight_kg=2.5,
    )

    sim = DroneDeliverySimulation(
        network=network,
        drones=[single_drone],
        requests=[req],
        dispatcher=fcfs_dispatcher,
        weather=extreme_weather,
    )
    sim.run(max_duration_min=60.0)

    event_types = [e["event_type"] for e in sim.events_log]
    assert "PACKAGE_DELIVERED" in event_types
    assert "RETURN_FAILED" in event_types
    assert "RETURNED_TO_DEPOT" not in event_types

    # 1. Customer delivery succeeded
    assert req.status == "DELIVERED"
    assert req.delivery_time_min is not None
    assert len(sim.completed_orders) == 1
    assert req in sim.completed_orders

    # 2. Prevent duplicate counting in failed_orders
    assert len(sim.failed_orders) == 0
    assert req not in sim.failed_orders

    # 3. Mission & return-leg failure recorded accurately
    assert req.mission_status == "RETURN_FAILED"
    assert req.failure_time_min is not None
    assert req.failure_time_min > req.delivery_time_min
    assert len(sim.return_failures) == 1
    assert len(sim.failed_missions) == 1
    assert len(sim.completed_missions) == 0

    # 4. Drone failure state recorded accurately
    assert single_drone.status == DroneStatus.FAILED_OUT_OF_BATTERY
    assert single_drone.battery.current_soc == 0.0
    assert single_drone.total_deliveries == 1
    assert single_drone.completed_missions == 0
    assert single_drone.failed_missions == 1
    assert single_drone.failure_time_min == req.failure_time_min

    metrics = sim.get_summary_metrics()
    assert metrics["delivered_orders"] == 1
    assert metrics["failed_orders"] == 0
    assert metrics["completed_missions"] == 0
    assert metrics["failed_missions"] == 1
    assert metrics["return_leg_failures"] == 1
    assert metrics["failed_drones"] == 1
    assert metrics["success_rate_pct"] == 100.0
    assert metrics["mission_success_rate_pct"] == 0.0


def test_outbound_leg_failure_accounting(
    network, single_drone: Drone, fcfs_dispatcher, extreme_weather
):
    """
    Verifies that when a drone runs out of battery on the outbound leg before reaching
    the destination:
    - Customer delivery fails (`status == "FAILED"`, in `failed_orders`, NOT in `completed_orders`).
    - Mission fails (`mission_status == "OUTBOUND_FAILED"`, in `failed_missions`, NOT in `return_failures`).
    """
    single_drone.battery.current_soc = 0.20  # 36 Wh < ~63.3 Wh needed for outbound leg
    req = DeliveryRequest(
        request_id="REQ-OUT-FAIL-01",
        destination_node="LOC-ANGARIA",
        arrival_time_min=0.0,
        package_weight_kg=2.5,
    )

    sim = DroneDeliverySimulation(
        network=network,
        drones=[single_drone],
        requests=[req],
        dispatcher=fcfs_dispatcher,
        weather=extreme_weather,
    )
    sim.run(max_duration_min=60.0)

    assert req.status == "FAILED"
    assert req.mission_status == "OUTBOUND_FAILED"
    assert req.delivery_time_min is None
    assert req.failure_time_min is not None
    assert len(sim.completed_orders) == 0
    assert len(sim.failed_orders) == 1
    assert len(sim.failed_missions) == 1
    assert len(sim.return_failures) == 0
    assert len(sim.completed_missions) == 0
    assert single_drone.status == DroneStatus.FAILED_OUT_OF_BATTERY


def test_reproducibility_with_fixed_random_seed(
    network, default_specs, bapa_dispatcher, temperate_weather
):
    """Verifies identical random seeds produce 100% identical requests, events, and metrics."""
    reqs_a = generate_synthetic_requests(network, num_requests=15, random_seed=42)
    reqs_b = generate_synthetic_requests(network, num_requests=15, random_seed=42)
    reqs_c = generate_synthetic_requests(network, num_requests=15, random_seed=99)

    assert reqs_a == reqs_b
    assert reqs_a != reqs_c

    fleet_a = [Drone(f"DRONE-{i+1:02d}", default_specs) for i in range(3)]
    fleet_b = [Drone(f"DRONE-{i+1:02d}", default_specs) for i in range(3)]

    sim_a = DroneDeliverySimulation(network, fleet_a, copy.deepcopy(reqs_a), bapa_dispatcher, temperate_weather)
    sim_b = DroneDeliverySimulation(network, fleet_b, copy.deepcopy(reqs_b), bapa_dispatcher, temperate_weather)

    sim_a.run(max_duration_min=240.0)
    sim_b.run(max_duration_min=240.0)

    assert sim_a.events_log == sim_b.events_log
    assert sim_a.get_summary_metrics() == sim_b.get_summary_metrics()

