"""
Spatial Network and Distance Calculator for Dumki Upazila Drone Air Corridors.
Uses Haversine distance formula and NetworkX graph topology.
"""
from __future__ import annotations
import json
import math
from typing import Dict, Any, Tuple
import networkx as nx
from src.config import NODES_FILE

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Computes great-circle distance between two GPS coordinates in kilometers.
    """
    r = 6371.0  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c

class DumkiNetwork:
    """Represents the spatial nodes, depots, and traversable air corridors in Dumki."""
    def __init__(self, nodes_file: str | None = None):
        path = nodes_file or str(NODES_FILE)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.depots: Dict[str, Dict[str, Any]] = {d["id"]: d for d in data["depots"]}
        self.delivery_nodes: Dict[str, Dict[str, Any]] = {n["id"]: n for n in data["delivery_nodes"]}
        self.all_nodes: Dict[str, Dict[str, Any]] = {**self.depots, **self.delivery_nodes}
        self.graph = nx.Graph()
        self._build_graph()

    def _build_graph(self):
        """Constructs a fully connected direct air corridor graph."""
        for node_id, info in self.all_nodes.items():
            self.graph.add_node(
                node_id,
                name=info["name"],
                lat=info["lat"],
                lon=info["lon"],
                type=info["type"]
            )

        # Build air corridors between all nodes
        node_ids = list(self.all_nodes.keys())
        for i in range(len(node_ids)):
            for j in range(i + 1, len(node_ids)):
                id1, id2 = node_ids[i], node_ids[j]
                n1, n2 = self.all_nodes[id1], self.all_nodes[id2]
                dist_km = haversine_distance(n1["lat"], n1["lon"], n2["lat"], n2["lon"])
                self.graph.add_edge(id1, id2, weight=dist_km, distance_km=round(dist_km, 3))

    def get_distance_km(self, origin_id: str, dest_id: str) -> float:
        """Returns the shortest flight distance between two nodes."""
        if origin_id == dest_id:
            return 0.0
        return self.graph[origin_id][dest_id]["distance_km"]

    def get_coordinates(self, node_id: str) -> Tuple[float, float]:
        """Returns (lat, lon) for a given node."""
        node = self.all_nodes[node_id]
        return node["lat"], node["lon"]

    def get_depot_id(self) -> str:
        """Returns the primary central depot ID."""
        return next(iter(self.depots.keys()))

