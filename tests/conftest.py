"""
Shared pytest fixtures for the Climate-Aware Intelligent Urban Drone Network test suite.
"""
import pytest
from src.config import DroneSpecs, WEATHER_SCENARIOS, WeatherScenario
from src.network import DumkiNetwork
from src.models import Drone, DeliveryRequest
from src.algorithms import FCFSDispatcher, BatteryAwareDispatcher


@pytest.fixture(scope="session")
def network() -> DumkiNetwork:
    """Loads the verified Dumki & PSTU spatial network."""
    return DumkiNetwork()


@pytest.fixture
def default_specs() -> DroneSpecs:
    """Returns default physical drone specifications."""
    return DroneSpecs()


@pytest.fixture
def temperate_weather() -> WeatherScenario:
    """Returns the Temperate baseline weather scenario."""
    return WEATHER_SCENARIOS["Temperate (Spring/Winter)"]


@pytest.fixture
def extreme_weather() -> WeatherScenario:
    """Returns the Extreme Monsoon / Heatwave weather scenario."""
    return WEATHER_SCENARIOS["Extreme Monsoon / Heatwave"]


@pytest.fixture
def single_drone(default_specs: DroneSpecs) -> Drone:
    """Returns a single initialized idle drone at DEPOT-PSTU."""
    return Drone(drone_id="DRONE-01", specs=default_specs)


@pytest.fixture
def drone_fleet(default_specs: DroneSpecs) -> list[Drone]:
    """Returns a 3-drone fleet initialized at DEPOT-PSTU."""
    return [Drone(drone_id=f"DRONE-{i+1:02d}", specs=default_specs) for i in range(3)]


@pytest.fixture
def fcfs_dispatcher() -> FCFSDispatcher:
    """Returns the baseline FCFS dispatcher."""
    return FCFSDispatcher()


@pytest.fixture
def bapa_dispatcher() -> BatteryAwareDispatcher:
    """Returns the proposed Battery-Aware (BAPA) dispatcher."""
    return BatteryAwareDispatcher()

