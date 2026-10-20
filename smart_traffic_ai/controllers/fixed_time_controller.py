from __future__ import annotations

from typing import Tuple


class FixedTimeController:
    """
    Conventional traffic signal controller operating on predetermined cycle lengths.
    Serves as the empirical baseline to evaluate RL agent improvements.
    """

    def __init__(self, green_duration: int = 20):
        self.green_duration = green_duration
        self.elapsed = 0

    def reset(self) -> None:
        self.elapsed = 0

    def select_action(self, time_step: int, current_phase: int) -> int:
        """
        Determines action based on fixed cycle:
        Even intervals prefer NS (0), odd intervals prefer EW (1).
        """
        cycle = (time_step // self.green_duration) % 2
        return 0 if cycle == 0 else 1
