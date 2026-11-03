"""Boundary discovery/loading is isolated from presentation and simulation logic."""
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import StudyArea

@dataclass
class BoundaryContext:
    geometry: Any | None
    message: str

def load_boundary_context() -> BoundaryContext:
    """Load only a locally supplied, reviewed Dumki polygon.

    A boundary file is deliberately opt-in: this prevents accidental use of an
    unverified geometry or a manually invented administrative boundary.
    """
    candidate = Path("data/boundaries/dumki_upazila_verified.geojson")
    if not candidate.exists():
        return BoundaryContext(None, "Showing approximate geographic viewing extent — no verified administrative boundary is currently bundled.")
    try:
        import geopandas as gpd
        frame = gpd.read_file(candidate)
        if frame.empty or not frame.geometry.is_valid.all():
            return BoundaryContext(None, "Verified-boundary file was rejected because its geometry is empty or invalid.")
        return BoundaryContext(frame.to_crs(4326).geometry.unary_union, "Verified Dumki administrative boundary loaded from local reviewed data.")
    except Exception as exc:
        return BoundaryContext(None, f"Boundary unavailable; showing approximate extent. ({type(exc).__name__})")
