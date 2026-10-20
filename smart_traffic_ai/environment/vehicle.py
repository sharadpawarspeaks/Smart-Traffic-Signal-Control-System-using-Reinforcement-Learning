from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


VEHICLE_CONFIGS = {
    "car": {
        "length": 4.5,
        "max_speed": 12.0,
        "accel": 2.5,
        "color": "#27d3e6",  # Cyan
        "pygame_color": (39, 211, 230),
    },
    "motorcycle": {
        "length": 2.2,
        "max_speed": 14.0,
        "accel": 3.5,
        "color": "#3182f6",  # Blue
        "pygame_color": (49, 130, 246),
    },
    "bus": {
        "length": 10.0,
        "max_speed": 8.5,
        "accel": 1.5,
        "color": "#f4b942",  # Amber
        "pygame_color": (244, 185, 66),
    },
    "ambulance": {
        "length": 6.0,
        "max_speed": 15.0,
        "accel": 3.0,
        "color": "#ff5d67",  # Red / White emergency
        "pygame_color": (255, 93, 103),
    },
    "fire_engine": {
        "length": 8.5,
        "max_speed": 13.0,
        "accel": 2.5,
        "color": "#ff3838",  # Fire red
        "pygame_color": (255, 56, 56),
    },
}


@dataclass
class Vehicle:
    id: int
    approach: int  # 0: North, 1: South, 2: East, 3: West
    vehicle_type: str = "car"
    position: float = 0.0  # Normalized: 0.0 (entry) to 1.0 (stop line) to >1.0 (cleared)
    speed: float = 0.0
    wait_time: float = 0.0
    crossed: bool = False
    emergency: bool = False

    def __post_init__(self):
        config = VEHICLE_CONFIGS.get(self.vehicle_type, VEHICLE_CONFIGS["car"])
        self.length = config["length"]
        self.max_speed = config["max_speed"]
        self.accel = config["accel"]
        self.color = config["color"]
        self.pygame_color = config["pygame_color"]
        if self.vehicle_type in ("ambulance", "fire_engine"):
            self.emergency = True

    def update_motion(self, can_move: bool, lead_vehicle: Vehicle | None = None, dt: float = 1.0) -> None:
        """
        Updates vehicle position and speed with safe car-following and stop line braking.
        """
        if self.crossed:
            self.position += 0.35 * dt
            return

        # Target position limit before stop line (stop line is at position 1.0)
        safe_stop_position = 0.96

        if lead_vehicle is not None:
            # Lead vehicle is ahead in the same approach
            # Keep at least safe distance behind lead vehicle
            safe_distance = 0.12  # normalized distance gap
            target_limit = max(0.0, lead_vehicle.position - safe_distance)
            can_move = can_move and (self.position < target_limit)
        else:
            target_limit = safe_stop_position

        if can_move:
            # Vehicle can accelerate or cruise forward
            self.position = min(1.3, self.position + 0.28 * dt)
            if self.position >= 1.0:
                self.crossed = True
            self.speed = self.max_speed
        else:
            # Must brake / wait behind lead vehicle or stop line
            if self.position < target_limit:
                self.position = min(target_limit, self.position + 0.08 * dt)
            self.speed = 0.0
            self.wait_time += dt
