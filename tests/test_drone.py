"""
Automated unit tests for Drone state lifecycle, mission assignment, completion, and availability.
"""
from src.models import Drone, DeliveryRequest, DroneStatus
from src.simulation import DroneDeliverySimulation


def test_initial_drone_state(single_drone: Drone):
    """Verifies initial drone attributes, battery SoC, and availability."""
    assert single_drone.drone_id == "DRONE-01"
    assert single_drone.status == DroneStatus.IDLE
    assert single_drone.current_node == "DEPOT-PSTU"
    assert single_drone.battery.current_soc == 1.0
    assert single_drone.battery.remaining_energy_wh == 180.0
    assert single_drone.total_deliveries == 0
    assert single_drone.completed_missions == 0
    assert single_drone.failed_missions == 0
    assert single_drone.total_distance_km == 0.0
    assert single_drone.total_energy_consumed_wh == 0.0
    assert single_drone.total_flight_time_min == 0.0
    assert single_drone.total_charging_wait_min == 0.0
    assert single_drone.current_request_id is None
    assert single_drone.failure_time_min is None
    assert single_drone.is_available() is True


def test_valid_state_transitions(single_drone: Drone):
    """Verifies valid transitions through all defined DroneStatus states."""
    for status in [
        DroneStatus.OUTBOUND_DELIVERY,
        DroneStatus.RETURNING,
        DroneStatus.WAITING_FOR_CHARGER,
        DroneStatus.CHARGING,
        DroneStatus.IDLE,
        DroneStatus.FAILED_OUT_OF_BATTERY,
    ]:
        single_drone.status = status
        assert single_drone.status == status
        if status == DroneStatus.IDLE:
            assert single_drone.is_available() is True
        else:
            assert single_drone.is_available() is False


def test_drone_availability_with_active_request(single_drone: Drone):
    """Verifies that a drone with an assigned request ID is marked unavailable."""
    assert single_drone.is_available() is True
    single_drone.current_request_id = "REQ-001"
    assert single_drone.is_available() is False
    single_drone.current_request_id = None
    assert single_drone.is_available() is True


def test_mission_assignment_locks_drone_immediately(
    network, single_drone: Drone, bapa_dispatcher, temperate_weather
):
    """Verifies that mission assignment immediately updates drone state to OUTBOUND_DELIVERY."""
    req = DeliveryRequest(
        request_id="REQ-ASSIGN-01",
        destination_node="LOC-PSTU-CSE",
        arrival_time_min=0.0,
        package_weight_kg=1.0,
    )
    sim = DroneDeliverySimulation(
        network=network,
        drones=[single_drone],
        requests=[req],
        dispatcher=bapa_dispatcher,
        weather=temperate_weather,
    )
    # Run just past dispatch at t=0.0 but before outbound flight finishes (~1.3 min)
    sim.run(max_duration_min=0.5)
    assert single_drone.status == DroneStatus.OUTBOUND_DELIVERY
    assert single_drone.current_request_id == "REQ-ASSIGN-01"
    assert single_drone.is_available() is False
    assert req.assigned_drone_id == "DRONE-01"
    assert req.status == "IN_TRANSIT"
    assert req.mission_status == "OUTBOUND"


def test_mission_completion_restores_drone_to_idle(
    network, single_drone: Drone, bapa_dispatcher, temperate_weather
):
    """Verifies full round-trip mission completion updates telemetry and restores IDLE state."""
    req = DeliveryRequest(
        request_id="REQ-COMPLETE-01",
        destination_node="LOC-PSTU-MED",
        arrival_time_min=0.0,
        package_weight_kg=1.0,
    )
    sim = DroneDeliverySimulation(
        network=network,
        drones=[single_drone],
        requests=[req],
        dispatcher=bapa_dispatcher,
        weather=temperate_weather,
    )
    sim.run(max_duration_min=30.0)

    assert single_drone.status == DroneStatus.IDLE
    assert single_drone.is_available() is True
    assert single_drone.current_node == "DEPOT-PSTU"
    assert single_drone.current_request_id is None
    assert single_drone.total_deliveries == 1
    assert single_drone.completed_missions == 1
    assert single_drone.failed_missions == 0
    assert single_drone.total_distance_km > 0.0
    assert single_drone.total_energy_consumed_wh > 0.0
    assert single_drone.total_flight_time_min > 0.0
    assert req.status == "DELIVERED"
    assert req.mission_status == "COMPLETED"
    assert req.return_time_min is not None

