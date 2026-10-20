from __future__ import annotations

from typing import Dict, List, Tuple


APPROACHES = ("North", "South", "East", "West")
APPROACH_INDICES = {"North": 0, "South": 1, "East": 2, "West": 3}

# Corridor groupings
CORRIDOR_NS = (0, 1)  # North and South
CORRIDOR_EW = (2, 3)  # East and West


class IntersectionLayout:
    """Represents a standard four-way traffic intersection."""

    def __init__(
        self,
        road_width: float = 140.0,
        approach_length: float = 300.0,
        num_lanes_per_direction: int = 1,
    ):
        self.road_width = road_width
        self.approach_length = approach_length
        self.num_lanes_per_direction = num_lanes_per_direction

    @staticmethod
    def get_approach_name(index: int) -> str:
        if 0 <= index < len(APPROACHES):
            return APPROACHES[index]
        return "Unknown"

    @staticmethod
    def get_corridor(approach_index: int) -> str:
        if approach_index in CORRIDOR_NS:
            return "NS"
        if approach_index in CORRIDOR_EW:
            return "EW"
        return "Unknown"
