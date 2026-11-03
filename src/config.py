"""
Configuration parameters for the Climate-Aware Intelligent Urban Drone Network Simulation.
Study Area: Dumki Upazila, Patuakhali, Bangladesh.
"""
from dataclasses import dataclass
from pathlib import Path

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
NODES_FILE = DATA_DIR / "dumki_nodes.json"

@dataclass(frozen=True)
class DroneSpecs:
    """Standardized multi-rotor delivery drone physical specifications."""
    cruising_speed_mps: float = 12.0          # Cruising speed in m/s (~43.2 km/h)
    takeoff_landing_time_s: float = 60.0       # Time overhead per takeoff/landing cycle (s)
    battery_capacity_wh: float = 180.0        # Rated battery capacity (Watt-hours)
    base_power_w: float = 210.0               # Hover/cruise baseline power consumption without payload (Watts)
    payload_power_coeff_w_per_kg: float = 45.0# Additional power consumption per kg of payload (W/kg)
    max_payload_kg: float = 2.5               # Maximum carrying capacity (kg)
    min_reserve_soc: float = 0.20             # Minimum safety battery reserve (20%)
    recharge_power_w: float = 300.0           # Charger power output (Watts)
    charging_efficiency: float = 0.90         # Electrical charging efficiency

@dataclass(frozen=True)
class WeatherScenario:
    """Weather scenario parameters influencing aerodynamics and battery efficiency."""
    name: str
    ambient_temp_c: float
    headwind_mps: float
    description: str

    @property
    def climate_multiplier(self) -> float:
        """
        Computes power consumption multiplier based on ambient temperature and wind.
        Reference baseline: 25°C, 0 m/s headwind -> multiplier = 1.0.
        Higher ambient temperature increases internal resistance and reduces air density.
        """
        temp_penalty = 0.015 * max(0.0, self.ambient_temp_c - 28.0)
        wind_penalty = 0.030 * self.headwind_mps
        return round(1.0 + temp_penalty + wind_penalty, 3)

WEATHER_SCENARIOS = {
    "Temperate (Spring/Winter)": WeatherScenario(
        name="Temperate",
        ambient_temp_c=26.0,
        headwind_mps=2.0,
        description="Mild coastal breeze, optimal battery operating range."
    ),
    "Moderate Summer": WeatherScenario(
        name="Moderate Summer",
        ambient_temp_c=32.0,
        headwind_mps=4.0,
        description="Warm tropical afternoon, moderate thermal strain on battery."
    ),
    "Extreme Monsoon / Heatwave": WeatherScenario(
        name="Extreme Heatwave",
        ambient_temp_c=39.0,
        headwind_mps=8.0,
        description="Severe summer heatwave & gusty coastal wind, high power drain."
    ),
}
