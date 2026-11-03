"""Deterministic illustrative relative-intensity generator; replaceable by a scientific model."""
from enum import Enum
import numpy as np
import pandas as pd
from .config import StudyArea

class Scenario(str, Enum):
    BASELINE = "Baseline Demo"
    GREEN = "Increased Green Space Demo"
    BUILT = "Increased Built-up Surface Demo"

def run_demo_simulation(area: StudyArea, scenario: Scenario, vegetation: float, built_up: float, resolution: int) -> pd.DataFrame:
    """Create deterministic grid cells with a purely illustrative 0–1 index."""
    lats = np.linspace(area.south, area.north, resolution + 1)
    lons = np.linspace(area.west, area.east, resolution + 1)
    rows = []
    scenario_offset = {Scenario.BASELINE: 0.0, Scenario.GREEN: -0.06, Scenario.BUILT: 0.08}[scenario]
    for i in range(resolution):
        for j in range(resolution):
            y, x = (i + .5) / resolution, (j + .5) / resolution
            spatial_pattern = .22 * np.sin(7*x + 1.3) * np.cos(6*y - .4) + .11 * np.cos(13*x*y)
            intensity = np.clip(.48 + spatial_pattern + .36*built_up - .26*vegetation + scenario_offset, 0, 1)
            rows.append({"south": lats[i], "north": lats[i+1], "west": lons[j], "east": lons[j+1], "lat": (lats[i]+lats[i+1])/2, "lon": (lons[j]+lons[j+1])/2, "intensity": float(intensity)})
    return pd.DataFrame(rows)
