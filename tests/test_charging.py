"""
Automated unit tests for Charging Station queues, bay capacity contention,
charging duration physics, and battery recharge limits.
"""
import pytest
from src.models import Drone, DeliveryRequest, DroneStatus
from src.simulation import DroneDeliverySimulation


def test_charging_triggered_below_threshold_and_recharges_to_full(
    network, single_drone: Drone, bapa_dispatcher, temperate_weather
):
    """
    Verifies that a drone returning with SoC < recharge_threshold_soc (0.50)
    enters the charging station, recharges to exactly 1.0 SoC, and returns to IDLE.
    """
    # Start drone at 0.52 SoC; short campus mission drops it below 0.50 SoC on return
    single_drone.battery.current_soc = 0.52
    req = DeliveryRequest(
        request_id="REQ-CHG-01",
        destination_node="LOC-PSTU-AGRI",
        arrival_time_min=0.0,
        package_weight_kg=1.5,
    )

    sim = DroneDeliverySimulation(
        network=network,
        drones=[single_drone],
        requests=[req],
        dispatcher=bapa_dispatcher,
        weather=temperate_weather,
        num_charging_bays=1,
        recharge_threshold_soc=0.50,
    )
    sim.run(max_duration_min=60.0)

    event_types = [e["event_type"] for e in sim.events_log]
    assert "CHARGING_QUEUE_ENTER" in event_types
    assert "CHARGING_STARTED" in event_types
    assert "CHARGING_COMPLETED" in event_types
    assert "DRONE_AVAILABLE" in event_types
    assert single_drone.battery.current_soc == 1.0
    assert single_drone.status == DroneStatus.IDLE


def test_charging_bay_capacity_and_queue_wait_time(
    network, drone_fleet: list[Drone], bapa_dispatcher, temperate_weather
):
    """
    Verifies charging bay capacity contention: when 3 drones return with SoC < 0.50
    and only 1 charging bay (capacity=1) exists, 2 drones must wait in queue.
    """
    for d in drone_fleet:
        d.battery.current_soc = 0.51

    requests = [
        DeliveryRequest(
            request_id=f"REQ-Q-{i+1}",
            destination_node="LOC-PSTU-HALLS",
            arrival_time_min=0.0,
            package_weight_kg=1.5,
        )
        for i in range(3)
    ]

    sim = DroneDeliverySimulation(
        network=network,
        drones=drone_fleet,
        requests=requests,
        dispatcher=bapa_dispatcher,
        weather=temperate_weather,
        num_charging_bays=1,
        recharge_threshold_soc=0.50,
    )
    sim.run(max_duration_min=120.0)

    wait_times = sorted(d.total_charging_wait_min for d in drone_fleet)
    # First drone gets the bay immediately (wait == 0); second and third wait sequentially
    assert pytest.approx(wait_times[0], abs=1e-4) == 0.0
    assert wait_times[1] > 15.0
    assert wait_times[2] > wait_times[1]

    for d in drone_fleet:
        assert d.battery.current_soc == 1.0
        assert d.status == DroneStatus.IDLE


def test_charging_skipped_when_soc_above_threshold(
    network, single_drone: Drone, bapa_dispatcher, temperate_weather
):
    """
    Verifies that a drone returning with SoC >= recharge_threshold_soc (0.50)
    does NOT enter the charging queue and immediately transitions to IDLE.
    """
    single_drone.battery.current_soc = 1.0
    req = DeliveryRequest(
        request_id="REQ-NOCHG-01",
        destination_node="LOC-PSTU-MED",
        arrival_time_min=0.0,
        package_weight_kg=0.5,
    )

    sim = DroneDeliverySimulation(
        network=network,
        drones=[single_drone],
        requests=[req],
        dispatcher=bapa_dispatcher,
        weather=temperate_weather,
        recharge_threshold_soc=0.50,
    )
    sim.run(max_duration_min=30.0)

    event_types = [e["event_type"] for e in sim.events_log]
    assert "CHARGING_QUEUE_ENTER" not in event_types
    assert "CHARGING_STARTED" not in event_types
    assert single_drone.battery.current_soc > 0.90
    assert single_drone.battery.current_soc < 1.0
    assert single_drone.status == DroneStatus.IDLE

