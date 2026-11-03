"""
Automated unit tests for dispatching algorithms (FCFSDispatcher, BatteryAwareDispatcher)
and spatial network corridor lookups.
"""
import pytest
from src.algorithms import BaseDispatcher, FCFSDispatcher, BatteryAwareDispatcher
from src.models import Drone, DeliveryRequest, DroneStatus
from src.config import DroneSpecs


def test_base_dispatcher_raises_not_implemented(network, single_drone, temperate_weather):
    """Verifies BaseDispatcher enforces subclass implementation of select_drone_for_request."""
    base = BaseDispatcher("Abstract")
    req = DeliveryRequest("REQ-01", "LOC-PSTU-CSE", 0.0, 1.0)
    with pytest.raises(NotImplementedError):
        base.select_drone_for_request(req, [single_drone], network, temperate_weather)


def test_fcfs_selects_first_idle_drone_at_depot(network, drone_fleet, fcfs_dispatcher, temperate_weather):
    """Verifies FCFS picks the first available IDLE drone located at the depot."""
    req = DeliveryRequest("REQ-FCFS-01", "LOC-PSTU-MED", 0.0, 1.0)
    drone_fleet[0].status = DroneStatus.OUTBOUND_DELIVERY
    drone_fleet[1].current_node = "LOC-PSTU-CSE"  # Not at depot

    selected = fcfs_dispatcher.select_drone_for_request(
        req, drone_fleet, network, temperate_weather
    )
    assert selected is drone_fleet[2]


def test_bapa_best_fit_minimum_surplus_selection(network, bapa_dispatcher, temperate_weather):
    """
    Verifies BAPA selects the feasible drone with the smallest post-mission SoC surplus
    above the 20% reserve threshold, preserving 100% charged drones for longer missions.
    """
    specs = DroneSpecs()
    d_full = Drone(drone_id="DRONE-FULL", specs=specs)
    d_full.battery.current_soc = 1.00

    d_mid = Drone(drone_id="DRONE-MID", specs=specs)
    d_mid.battery.current_soc = 0.45

    d_low = Drone(drone_id="DRONE-LOW", specs=specs)
    d_low.battery.current_soc = 0.21  # Insufficient for trip + 0.20 reserve

    req_short = DeliveryRequest(
        request_id="REQ-SHORT",
        destination_node="LOC-PSTU-CSE",  # 0.22 km (~4.5% round-trip SoC)
        arrival_time_min=0.0,
        package_weight_kg=1.0,
    )

    selected = bapa_dispatcher.select_drone_for_request(
        req_short, [d_full, d_mid, d_low], network, temperate_weather
    )
    # DRONE-MID (0.45 SoC) is feasible and leaves smaller surplus than DRONE-FULL (1.00 SoC)
    assert selected is d_mid


def test_payload_capacity_constraint_enforced(network, single_drone, fcfs_dispatcher, bapa_dispatcher, temperate_weather):
    """Verifies requests exceeding DroneSpecs.max_payload_kg (2.5 kg) are not assigned."""
    overweight_req = DeliveryRequest(
        request_id="REQ-HEAVY",
        destination_node="LOC-PSTU-CSE",
        arrival_time_min=0.0,
        package_weight_kg=3.5,  # Exceeds 2.5 kg max payload
    )
    assert bapa_dispatcher.select_drone_for_request(
        overweight_req, [single_drone], network, temperate_weather
    ) is None
    assert fcfs_dispatcher.select_drone_for_request(
        overweight_req, [single_drone], network, temperate_weather
    ) is None


def test_spatial_network_direct_corridor_distances(network):
    """Verifies Haversine direct corridor graph properties in DumkiNetwork."""
    depot_id = network.get_depot_id()
    assert depot_id == "DEPOT-PSTU"
    assert len(network.delivery_nodes) == 10
    assert network.get_distance_km(depot_id, depot_id) == 0.0

    # Closest node: LOC-PSTU-MED (~0.205 km); Farthest node: LOC-ANGARIA (~5.338 km)
    d_med = network.get_distance_km(depot_id, "LOC-PSTU-MED")
    d_ang = network.get_distance_km(depot_id, "LOC-ANGARIA")
    assert 0.15 < d_med < 0.30
    assert 5.20 < d_ang < 5.50
    assert d_med < d_ang
    # Symmetry check
    assert network.get_distance_km("LOC-PSTU-MED", depot_id) == d_med

