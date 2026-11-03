"""
Synthetic Delivery Request Generator for Dumki Upazila.
Simulates realistic medical and emergency package arrivals using a Poisson process.
"""
from __future__ import annotations
import random
from typing import List
from src.models import DeliveryRequest
from src.network import DumkiNetwork

def generate_synthetic_requests(
    network: DumkiNetwork,
    num_requests: int = 30,
    arrival_rate_per_hour: float = 6.0,
    min_weight_kg: float = 0.5,
    max_weight_kg: float = 2.5,
    random_seed: int = 42
) -> List[DeliveryRequest]:
    """
    Generates a reproducible list of delivery requests.
    Arrival intervals follow an exponential distribution (Poisson arrival process).
    """
    rng = random.Random(random_seed)
    delivery_node_ids = list(network.delivery_nodes.keys())
    requests: List[DeliveryRequest] = []
    
    current_time_min = 0.0
    mean_interval_min = 60.0 / arrival_rate_per_hour

    for i in range(num_requests):
        # Exponential inter-arrival time
        inter_arrival = rng.expovariate(1.0 / mean_interval_min)
        current_time_min += inter_arrival
        
        destination = rng.choice(delivery_node_ids)
        weight = round(rng.uniform(min_weight_kg, max_weight_kg), 2)
        
        req = DeliveryRequest(
            request_id=f"REQ-{i+1:03d}",
            destination_node=destination,
            arrival_time_min=round(current_time_min, 2),
            package_weight_kg=weight,
            urgency_deadline_min=round(current_time_min + rng.uniform(45.0, 90.0), 2)
        )
        requests.append(req)

    return requests

