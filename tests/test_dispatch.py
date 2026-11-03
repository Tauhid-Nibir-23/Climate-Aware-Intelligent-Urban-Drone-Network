"""
Automated tests for dispatch concurrency lock (Bug #1 regression), simultaneous arrivals,
queue behavior, and FCFS vs BAPA dispatch policies.
"""
from src.models import Drone, DeliveryRequest, DroneStatus
from src.simulation import DroneDeliverySimulation


def test_bug1_regression_no_duplicate_simultaneous_assignment(
    network, single_drone: Drone, fcfs_dispatcher, temperate_weather
):
    """
    Regression test for Bug #1:
    - Two delivery requests arrive at the exact same simulation time (t = 0.0).
    - Only one drone (DRONE-01) is available.
    - Verify that DRONE-01 receives only one mission at t = 0.0.
    - Verify that its status immediately becomes OUTBOUND_DELIVERY.
    - Verify that the second request remains queued in pending_orders until DRONE-01 finishes.
    """
    req1 = DeliveryRequest(
        request_id="REQ-SIM-01",
        destination_node="LOC-DUMKI-HOSP",
        arrival_time_min=0.0,
        package_weight_kg=1.0,
    )
    req2 = DeliveryRequest(
        request_id="REQ-SIM-02",
        destination_node="LOC-DUMKI-BAZAR",
        arrival_time_min=0.0,
        package_weight_kg=1.2,
    )

    sim = DroneDeliverySimulation(
        network=network,
        drones=[single_drone],
        requests=[req1, req2],
        dispatcher=fcfs_dispatcher,
        weather=temperate_weather,
    )

    # Run until t = 0.5 min (after dispatch at t = 0.0, while DRONE-01 is still flying outbound)
    sim.run(max_duration_min=0.5)

    dispatch_events_at_zero = [
        e for e in sim.events_log
        if e["event_type"] == "MISSION_DISPATCH" and e["simulation_time_min"] == 0.0
    ]
    assert len(dispatch_events_at_zero) == 1
    assert single_drone.status == DroneStatus.OUTBOUND_DELIVERY
    assert single_drone.current_request_id == "REQ-SIM-01"

    # First request is in transit; second request must remain queued in pending_orders
    assert req1.status == "IN_TRANSIT"
    assert req1.assigned_drone_id == "DRONE-01"
    assert req2.status == "PENDING"
    assert req2.assigned_drone_id is None
    assert req2 in sim.pending_orders


def test_simultaneous_requests_sequential_completion_with_single_drone(
    network, single_drone: Drone, bapa_dispatcher, temperate_weather
):
    """
    Verifies that when 3 requests arrive at the same timestamp with 1 available drone,
    they are executed strictly sequentially without overlapping flight intervals.
    """
    requests = [
        DeliveryRequest(
            request_id=f"REQ-SEQ-{i+1}",
            destination_node="LOC-PSTU-CSE",
            arrival_time_min=2.0,
            package_weight_kg=1.0,
        )
        for i in range(3)
    ]

    sim = DroneDeliverySimulation(
        network=network,
        drones=[single_drone],
        requests=requests,
        dispatcher=bapa_dispatcher,
        weather=temperate_weather,
    )
    sim.run(max_duration_min=60.0)

    assert len(sim.completed_orders) == 3
    assert len(sim.completed_missions) == 3
    assert len(sim.pending_orders) == 0

    dispatch_times = [
        e["simulation_time_min"]
        for e in sim.events_log
        if e["event_type"] == "MISSION_DISPATCH"
    ]
    return_times = [
        e["simulation_time_min"]
        for e in sim.events_log
        if e["event_type"] == "RETURNED_TO_DEPOT"
    ]
    assert len(dispatch_times) == 3
    assert len(return_times) == 3
    # Every subsequent dispatch must occur at or after the previous mission returned to depot
    assert dispatch_times[1] >= return_times[0]
    assert dispatch_times[2] >= return_times[1]


def test_multiple_simultaneous_requests_across_multi_drone_fleet(
    network, drone_fleet: list[Drone], bapa_dispatcher, temperate_weather
):
    """
    Verifies that when 5 requests arrive simultaneously at t = 0.0 and 3 drones are available,
    exactly 3 unique drones are dispatched at t = 0.0 and 2 requests remain queued.
    """
    requests = [
        DeliveryRequest(
            request_id=f"REQ-BATCH-{i+1}",
            destination_node="LOC-PSTU-HALLS",
            arrival_time_min=0.0,
            package_weight_kg=1.0,
        )
        for i in range(5)
    ]

    sim = DroneDeliverySimulation(
        network=network,
        drones=drone_fleet,
        requests=requests,
        dispatcher=bapa_dispatcher,
        weather=temperate_weather,
    )
    sim.run(max_duration_min=0.5)

    dispatched_reqs = [r for r in requests if r.status == "IN_TRANSIT"]
    queued_reqs = [r for r in requests if r.status == "PENDING"]

    assert len(dispatched_reqs) == 3
    assert len(queued_reqs) == 2
    assert len(sim.pending_orders) == 2

    assigned_drones = {r.assigned_drone_id for r in dispatched_reqs}
    assert len(assigned_drones) == 3  # All 3 assigned drones are distinct


def test_fcfs_vs_bapa_infeasible_order_queue_holding(
    network, single_drone: Drone, fcfs_dispatcher, bapa_dispatcher, extreme_weather
):
    """
    Verifies that when a drone has 55% SoC and a long-range order to LOC-ANGARIA arrives:
    - BAPA holds the order safely in pending_orders because round-trip + reserve > 55%.
    - FCFS naively dispatches the drone immediately.
    """
    req = DeliveryRequest(
        request_id="REQ-HOLD-01",
        destination_node="LOC-ANGARIA",
        arrival_time_min=0.0,
        package_weight_kg=2.5,
    )
    single_drone.battery.current_soc = 0.55

    assert bapa_dispatcher.select_drone_for_request(
        req, [single_drone], network, extreme_weather
    ) is None
    assert fcfs_dispatcher.select_drone_for_request(
        req, [single_drone], network, extreme_weather
    ) is single_drone

