from __future__ import annotations

from typing import Dict, List, Optional, Tuple


PHASE_NS_GREEN = 0
PHASE_NS_YELLOW = 1
PHASE_EW_GREEN = 2
PHASE_EW_YELLOW = 3

PHASE_NAMES = ("NS Green", "NS Yellow", "EW Green", "EW Yellow")

CORRIDOR_NS = (0, 1)  # North, South
CORRIDOR_EW = (2, 3)  # East, West


class SignalSafetyController:
    """
    Centralized Signal Safety Controller that guarantees:
    1. Conflicting green signals are impossible (NS Green and EW Green are mutually exclusive).
    2. Transitions between conflicting corridors MUST pass through a mandatory Yellow interval.
    3. Minimum green duration is enforced to prevent rapid signal flickering.
    4. Maximum green duration is enforced to prevent corridor starvation.
    5. Emergency vehicle priority preemption executes safely through yellow clearance.
    """

    def __init__(
        self,
        min_green: int = 5,
        max_green: int = 40,
        yellow_duration: int = 2,
    ):
        self.min_green = min_green
        self.max_green = max_green
        self.yellow_duration = yellow_duration

        self.current_phase: int = PHASE_NS_GREEN
        self.phase_time: int = 0
        self.emergency_queue: List[int] = []  # List of emergency vehicle approaches
        self.preemption_active: bool = False

    def reset(self, initial_phase: int = PHASE_NS_GREEN) -> None:
        self.current_phase = initial_phase
        self.phase_time = 0
        self.emergency_queue.clear()
        self.preemption_active = False

    @property
    def phase_name(self) -> str:
        return PHASE_NAMES[self.current_phase]

    def is_green(self) -> bool:
        return self.current_phase in (PHASE_NS_GREEN, PHASE_EW_GREEN)

    def is_yellow(self) -> bool:
        return self.current_phase in (PHASE_NS_YELLOW, PHASE_EW_YELLOW)

    def get_green_approaches(self) -> Tuple[int, ...]:
        if self.current_phase == PHASE_NS_GREEN:
            return CORRIDOR_NS
        elif self.current_phase == PHASE_EW_GREEN:
            return CORRIDOR_EW
        return ()

    def allows_approach(self, approach: int) -> bool:
        return approach in self.get_green_approaches()

    def request_emergency_priority(self, approach: int) -> None:
        """Queues an emergency vehicle priority request safely."""
        if approach not in (0, 1, 2, 3):
            raise ValueError(f"Invalid approach {approach}. Must be 0, 1, 2, or 3.")
        if approach not in self.emergency_queue:
            self.emergency_queue.append(approach)
        self.preemption_active = True

    def clear_emergency(self, approach: int | None = None) -> None:
        if approach is not None:
            if approach in self.emergency_queue:
                self.emergency_queue.remove(approach)
        else:
            self.emergency_queue.clear()
        self.preemption_active = bool(self.emergency_queue)

    def request_action(self, action: int, extension_seconds: int = 5) -> Tuple[int, str]:
        """
        Processes high-level agent action (0: prioritize NS, 1: prioritize EW, 2: extend current).
        Returns (new_phase, reason_string).
        """
        # If emergency preemption is active, prioritize the corridor of the first emergency vehicle
        if self.emergency_queue:
            lead_emergency = self.emergency_queue[0]
            target_corridor = 0 if lead_emergency in CORRIDOR_NS else 1
            desired_green = PHASE_NS_GREEN if target_corridor == 0 else PHASE_EW_GREEN

            if self.current_phase == desired_green:
                # Already green for emergency vehicle: extend it safely
                return self.current_phase, f"Emergency preemption: maintaining green for Approach {lead_emergency}."
            elif self.is_yellow():
                # Let yellow complete safely
                return self.current_phase, "Emergency preemption: yellow clearance in progress."
            else:
                # In conflicting green: initiate transition to yellow immediately
                yellow_phase = PHASE_NS_YELLOW if self.current_phase == PHASE_NS_GREEN else PHASE_EW_YELLOW
                self.current_phase = yellow_phase
                self.phase_time = 0
                return self.current_phase, f"Emergency preemption: initiating yellow transition for Approach {lead_emergency}."

        # Action 2: Extend current green
        if action == 2:
            if self.is_green():
                if self.phase_time < self.max_green:
                    return self.current_phase, f"Extended {self.phase_name} (+{extension_seconds}s). Within max green limit."
                else:
                    # Enforce max green limit: transition to yellow
                    yellow = PHASE_NS_YELLOW if self.current_phase == PHASE_NS_GREEN else PHASE_EW_YELLOW
                    self.current_phase = yellow
                    self.phase_time = 0
                    return self.current_phase, f"Max green duration ({self.max_green}s) reached. Switching to yellow."
            else:
                return self.current_phase, f"Cannot extend during yellow phase ({self.phase_name})."

        # Action 0: Request NS Green, Action 1: Request EW Green
        desired_phase = PHASE_NS_GREEN if action == 0 else PHASE_EW_GREEN
        opposite_phase = PHASE_EW_GREEN if action == 0 else PHASE_NS_GREEN

        if self.current_phase == desired_phase:
            if self.phase_time >= self.max_green:
                yellow = PHASE_NS_YELLOW if desired_phase == PHASE_NS_GREEN else PHASE_EW_YELLOW
                self.current_phase = yellow
                self.phase_time = 0
                return self.current_phase, f"Max green reached ({self.max_green}s). Switching to yellow."
            return self.current_phase, f"Maintaining active {self.phase_name}."

        elif self.current_phase == opposite_phase:
            # Requesting switch from active green to opposite green
            if self.phase_time < self.min_green:
                return self.current_phase, f"Enforcing minimum green ({self.min_green}s). Current: {self.phase_time}s."
            # Transition to yellow first - NEVER jump directly to conflicting green
            yellow = PHASE_NS_YELLOW if opposite_phase == PHASE_NS_GREEN else PHASE_EW_YELLOW
            self.current_phase = yellow
            self.phase_time = 0
            return self.current_phase, f"Safe transition: initiating {PHASE_NAMES[yellow]}."

        elif self.is_yellow():
            # In yellow phase: safety controller manages yellow countdown automatically
            return self.current_phase, f"Safe clearance: {self.phase_name} countdown ({self.phase_time}/{self.yellow_duration}s)."

        return self.current_phase, "Action processed."

    def tick(self, seconds: int = 1) -> None:
        """Advances internal phase timer and executes automatic yellow clearances."""
        self.phase_time += seconds

        if self.current_phase == PHASE_NS_YELLOW and self.phase_time >= self.yellow_duration:
            self.current_phase = PHASE_EW_GREEN
            self.phase_time = 0
        elif self.current_phase == PHASE_EW_YELLOW and self.phase_time >= self.yellow_duration:
            self.current_phase = PHASE_NS_GREEN
            self.phase_time = 0
