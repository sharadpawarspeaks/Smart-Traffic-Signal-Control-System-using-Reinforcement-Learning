from __future__ import annotations

import random
from typing import Dict, List, Optional
from smart_traffic_ai.environment.vehicle import Vehicle


TRAFFIC_PRESETS = {
    "Low": (0.10, 0.09, 0.08, 0.07),
    "Medium": (0.22, 0.20, 0.18, 0.16),
    "High": (0.35, 0.32, 0.30, 0.28),
}


class TrafficGenerator:
    """
    Generates realistic vehicle traffic approaching from North, South, East, and West.
    Generates a mix of vehicle types (cars, motorcycles, buses) and handles emergency vehicle requests.
    """

    def __init__(
        self,
        arrival_rates: tuple[float, float, float, float] = (0.22, 0.20, 0.18, 0.16),
        seed: int | None = None,
    ):
        self.arrival_rates = list(arrival_rates)
        self.rng = random.Random(seed)
        self.next_vehicle_id = 1

    def set_seed(self, seed: int | None) -> None:
        self.rng.seed(seed)

    def set_arrival_rates(self, rates: tuple[float, float, float, float]) -> None:
        self.arrival_rates = list(rates)

    def set_preset(self, preset_name: str) -> None:
        if preset_name in TRAFFIC_PRESETS:
            self.arrival_rates = list(TRAFFIC_PRESETS[preset_name])

    def spawn_vehicles(self) -> List[Vehicle]:
        """Checks arrival probabilities for each approach and generates vehicles."""
        new_vehicles = []
        for approach, rate in enumerate(self.arrival_rates):
            if self.rng.random() < rate:
                # Vehicle type distribution: 70% car, 18% motorcycle, 12% bus
                p = self.rng.random()
                if p < 0.70:
                    v_type = "car"
                elif p < 0.88:
                    v_type = "motorcycle"
                else:
                    v_type = "bus"

                vehicle = Vehicle(
                    id=self.next_vehicle_id,
                    approach=approach,
                    vehicle_type=v_type,
                    position=0.0,
                )
                self.next_vehicle_id += 1
                new_vehicles.append(vehicle)
        return new_vehicles

    def create_emergency_vehicle(self, approach: int, vehicle_type: str = "ambulance") -> Vehicle:
        """Explicitly spawns an emergency vehicle on the designated approach."""
        if vehicle_type not in ("ambulance", "fire_engine"):
            vehicle_type = "ambulance"
        vehicle = Vehicle(
            id=self.next_vehicle_id,
            approach=approach,
            vehicle_type=vehicle_type,
            position=0.0,
            emergency=True,
        )
        self.next_vehicle_id += 1
        return vehicle
