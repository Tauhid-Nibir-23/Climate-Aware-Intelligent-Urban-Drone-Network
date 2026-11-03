"""
Automated unit tests for Battery physics, discharge/recharge boundaries, negative energy handling,
and safety reserve constraints.
"""
import pytest
from src.models import Battery, Drone, DeliveryRequest
from src.config import DroneSpecs


def test_battery_decreases_after_flight():
    """Verifies battery SoC and remaining Wh decrease accurately after flight discharge."""
    specs = DroneSpecs()
    battery = Battery(capacity_wh=specs.battery_capacity_wh, current_soc=1.0)

    energy_wh = battery.calculate_trip_energy_wh(
        distance_km=5.0,
        speed_mps=specs.cruising_speed_mps,
        payload_kg=0.0,
        base_power_w=specs.base_power_w,
        payload_power_coeff=specs.payload_power_coeff_w_per_kg,
        climate_multiplier=1.0,
        maneuver_time_s=specs.takeoff_landing_time_s,
    )
    # 5 km at 12 m/s = 416.67s + 60s = 476.67s = 0.132407 hr; 210W * 0.132407 hr = 27.8056 Wh
    assert pytest.approx(energy_wh, rel=1e-3) == 27.81

    survived = battery.discharge(energy_wh)
    assert survived is True
    assert battery.current_soc < 1.0
    assert pytest.approx(battery.remaining_energy_wh, rel=1e-3) == 180.0 - energy_wh


def test_battery_payload_and_climate_scaling():
    """Verifies mass-dependent induced power and climate multiplier scaling."""
    specs = DroneSpecs()
    battery = Battery(capacity_wh=specs.battery_capacity_wh, current_soc=1.0)

    loaded_wh = battery.calculate_trip_energy_wh(
        distance_km=5.0,
        speed_mps=specs.cruising_speed_mps,
        payload_kg=2.5,
        base_power_w=specs.base_power_w,
        payload_power_coeff=specs.payload_power_coeff_w_per_kg,
        climate_multiplier=1.0,
        maneuver_time_s=specs.takeoff_landing_time_s,
    )
    # (210 + 45*2.5) = 322.5W * (476.667/3600) = 42.70 Wh
    assert pytest.approx(loaded_wh, rel=1e-3) == 42.70

    heatwave_wh = battery.calculate_trip_energy_wh(
        distance_km=5.0,
        speed_mps=specs.cruising_speed_mps,
        payload_kg=2.5,
        base_power_w=specs.base_power_w,
        payload_power_coeff=specs.payload_power_coeff_w_per_kg,
        climate_multiplier=1.405,
        maneuver_time_s=specs.takeoff_landing_time_s,
    )
    assert pytest.approx(heatwave_wh, rel=1e-3) == 60.00


def test_battery_cannot_exceed_capacity():
    """Verifies battery SoC is clamped to [0.0, 1.0] on initialization and recharge."""
    battery = Battery(capacity_wh=180.0, current_soc=0.60)
    battery.recharge(500.0)  # Huge recharge amount
    assert battery.current_soc == 1.0
    assert battery.remaining_energy_wh == 180.0

    over_init = Battery(capacity_wh=180.0, current_soc=1.5)
    assert over_init.current_soc == 1.0

    under_init = Battery(capacity_wh=180.0, current_soc=-0.5)
    assert under_init.current_soc == 0.0


def test_invalid_negative_energy_is_handled():
    """Verifies negative energy values and invalid parameters raise ValueError."""
    battery = Battery(capacity_wh=180.0, current_soc=0.8)

    with pytest.raises(ValueError):
        battery.discharge(-15.0)

    with pytest.raises(ValueError):
        battery.recharge(-15.0)

    with pytest.raises(ValueError):
        Battery(capacity_wh=0.0)

    with pytest.raises(ValueError):
        Battery(capacity_wh=-100.0)

    with pytest.raises(ValueError):
        battery.calculate_trip_energy_wh(
            distance_km=-1.0,
            speed_mps=12.0,
            payload_kg=1.0,
            base_power_w=210.0,
            payload_power_coeff=45.0,
        )

    with pytest.raises(ValueError):
        battery.calculate_trip_energy_wh(
            distance_km=1.0,
            speed_mps=0.0,
            payload_kg=1.0,
            base_power_w=210.0,
            payload_power_coeff=45.0,
        )

    with pytest.raises(ValueError):
        battery.calculate_trip_energy_wh(
            distance_km=1.0,
            speed_mps=12.0,
            payload_kg=-0.5,
            base_power_w=210.0,
            payload_power_coeff=45.0,
        )


def test_reserve_constraint_and_insufficient_battery_prevents_infeasible_mission(
    network, single_drone: Drone, bapa_dispatcher, extreme_weather
):
    """
    Verifies that BAPA enforces the 20% safety reserve constraint and rejects a mission
    when the drone's battery would drop below min_reserve_soc (0.20).
    """
    req_far = DeliveryRequest(
        request_id="REQ-FAR-01",
        destination_node="LOC-ANGARIA",  # 5.34 km away (~58.3% round-trip SoC in extreme weather)
        arrival_time_min=0.0,
        package_weight_kg=2.5,
    )

    # Set drone SoC to 0.70: enough to survive the round-trip (~0.583 SoC needed -> 0.117 final SoC),
    # but violates the 0.20 min_reserve_soc requirement (requires >= 0.783 SoC).
    single_drone.battery.current_soc = 0.70
    selected = bapa_dispatcher.select_drone_for_request(
        req_far, [single_drone], network, extreme_weather
    )
    assert selected is None

    # Set drone SoC to 0.85: leaves ~0.267 SoC >= 0.20 reserve -> feasible!
    single_drone.battery.current_soc = 0.85
    selected_ok = bapa_dispatcher.select_drone_for_request(
        req_far, [single_drone], network, extreme_weather
    )
    assert selected_ok is single_drone

