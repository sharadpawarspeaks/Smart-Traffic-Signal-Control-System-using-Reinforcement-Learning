from __future__ import annotations

import random
from typing import Dict, List, Optional, Tuple
import numpy as np

from smart_traffic_ai.environment.vehicle import Vehicle
from smart_traffic_ai.environment.intersection import APPROACHES, CORRIDOR_NS, CORRIDOR_EW
from smart_traffic_ai.controllers.signal_controller import (
    SignalSafetyController,
    PHASE_NS_GREEN,
    PHASE_NS_YELLOW,
    PHASE_EW_GREEN,
    PHASE_EW_YELLOW,
    PHASE_NAMES,
)
from smart_traffic_ai.simulation.traffic_generator import TrafficGenerator
from smart_traffic_ai.services.metrics_service import MetricsService, RewardBreakdown, FairnessMetrics


class TrafficEnvironment:
    """
    Intelligent four-way traffic intersection simulation environment.
    Enforces centralized signal safety, car-following physics, and transparent Q-learning rewards.
    """

    def __init__(
        self,
        seed: int | None = None,
        arrival_rates: tuple[float, float, float, float] | list[float] | None = None,
        control_interval: int = 5,
        min_green: int = 5,
        max_green: int = 35,
        yellow_duration: int = 2,
        weight_pass: float = 3.0,
        weight_wait: float = 0.20,
        weight_queue: float = 0.05,
        weight_switch: float = 0.40,
        weight_starve: float = 0.10,
    ):
        self.seed = seed
        self.arrival_rates = list(arrival_rates or (0.22, 0.20, 0.18, 0.16))
        self.control_interval = control_interval
        self.max_steps = 600

        # Reward weights
        self.weight_pass = weight_pass
        self.weight_wait = weight_wait
        self.weight_queue = weight_queue
        self.weight_switch = weight_switch
        self.weight_starve = weight_starve

        # Subsystems
        self.signal_controller = SignalSafetyController(
            min_green=min_green,
            max_green=max_green,
            yellow_duration=yellow_duration,
        )
        self.generator = TrafficGenerator(arrival_rates=tuple(self.arrival_rates), seed=seed)
        self.metrics_service = MetricsService()
        self.rng = random.Random(seed)

        self.reset(seed=seed)

    @property
    def phase(self) -> int:
        return self.signal_controller.current_phase

    @phase.setter
    def phase(self, value: int) -> None:
        self.signal_controller.current_phase = value

    @property
    def phase_time(self) -> int:
        return self.signal_controller.phase_time

    @phase_time.setter
    def phase_time(self, value: int) -> None:
        self.signal_controller.phase_time = value

    def reset(self, seed: int | None = None) -> Tuple[tuple, dict]:
        if seed is not None:
            self.seed = seed
            self.rng.seed(seed)
            self.generator.set_seed(seed)

        self.time = 0
        self.signal_controller.reset(initial_phase=PHASE_NS_GREEN)
        self.vehicles: List[Vehicle] = []
        self.total_wait = 0.0
        self.total_passed = 0
        self.episode_reward = 0.0
        self.history: List[dict] = []
        self.emergency_approach: int | None = None
        self.last_decision_reason: str = "Simulation initialized."
        self.metrics_service.reset()

        return self.get_state(), self.get_metrics()

    def request_emergency(self, approach: int, vehicle_type: str = "ambulance") -> None:
        """Spawns an emergency vehicle and registers safety preemption."""
        if approach not in range(4):
            raise ValueError("emergency approach must be 0 (North), 1 (South), 2 (East), or 3 (West)")
        self.emergency_approach = approach
        self.signal_controller.request_emergency_priority(approach)
        ev = self.generator.create_emergency_vehicle(approach, vehicle_type=vehicle_type)
        self.vehicles.append(ev)

    def get_state(self) -> tuple:
        """
        Discretized state representation for tabular Q-learning:
        (North_cat, South_cat, East_cat, West_cat, phase)
        where categories are: 0: Low (0-4), 1: Med (5-9), 2: High (10+)
        """
        queues = self._queues()
        buckets = tuple(min(2, q // 5) for q in queues)
        return (*buckets, self.signal_controller.current_phase)

    def step(self, action: int) -> Tuple[tuple, float, bool, dict]:
        """
        Advances the simulation by control_interval seconds using the selected action.
        """
        if action not in (0, 1, 2):
            raise ValueError(f"action must be 0 (North-South), 1 (East-West), or 2 (Extend). Got: {action}")

        previous_wait = self.total_wait
        previous_passed = self.total_passed
        previous_phase = self.signal_controller.current_phase

        # 1. Route action through Signal Safety Controller
        new_phase, reason = self.signal_controller.request_action(action, extension_seconds=self.control_interval)
        self.last_decision_reason = reason

        # 2. Advance simulation second-by-second across control_interval
        for _ in range(self.control_interval):
            # Spawn incoming vehicles
            new_incoming = self.generator.spawn_vehicles()
            self.vehicles.extend(new_incoming)

            # Move vehicles and update positions
            self._move_one_second()

            # Advance safety controller timer (handles yellow intervals)
            self.signal_controller.tick(seconds=1)
            self.time += 1

        # 3. Compute Transparent Reward Formulation
        wait_delta = self.total_wait - previous_wait
        pass_delta = self.total_passed - previous_passed
        queues = self._queues()
        fairness = self.metrics_service.compute_fairness(self.vehicles, queues)

        pass_reward = pass_delta * self.weight_pass
        wait_penalty = wait_delta * self.weight_wait
        queue_penalty = sum(queues) * self.weight_queue
        switch_penalty = self.weight_switch if previous_phase != self.signal_controller.current_phase else 0.0
        starve_penalty = (fairness.max_individual_wait * self.weight_starve) if fairness.is_starved else 0.0

        reward = pass_reward - wait_penalty - queue_penalty - switch_penalty - starve_penalty
        self.episode_reward += reward

        breakdown = RewardBreakdown(
            pass_reward=pass_reward,
            wait_penalty=wait_penalty,
            queue_penalty=queue_penalty,
            switch_penalty=switch_penalty,
            starvation_penalty=starve_penalty,
            total_reward=reward,
        )

        metrics = self.get_metrics()
        self.metrics_service.record_step(
            time_step=self.time,
            queues=queues,
            avg_wait=float(metrics["average_wait"]),
            passed_count=self.total_passed,
            reward=reward,
            breakdown=breakdown,
        )

        done = self.time >= self.max_steps
        info = {
            "phase_name": self.signal_controller.phase_name,
            "queues": queues,
            "emergency_priority": self.signal_controller.preemption_active,
            "decision_reason": self.last_decision_reason,
            "reward_breakdown": breakdown,
            "fairness": fairness,
        }

        # Check if emergency vehicles have cleared
        active_emergencies = [v for v in self.vehicles if v.emergency and not v.crossed]
        if not active_emergencies:
            self.signal_controller.clear_emergency()
            self.emergency_approach = None
        else:
            self.emergency_approach = active_emergencies[0].approach

        return self.get_state(), reward, done, info

    def _move_one_second(self) -> None:
        """Moves vehicles along their approaches respecting traffic signals and car-following."""
        passed_vehicles: List[Vehicle] = []

        # Sort vehicles in each approach by position descending (closest to intersection first)
        for approach in range(4):
            approach_vehicles = [v for v in self.vehicles if v.approach == approach]
            approach_vehicles.sort(key=lambda v: v.position, reverse=True)

            can_signal_move = self.signal_controller.allows_approach(approach)

            lead_veh = None
            for veh in approach_vehicles:
                # If vehicle is before stop line (position < 1.0), movement depends on signal
                if not veh.crossed:
                    can_veh_move = can_signal_move
                else:
                    can_veh_move = True  # Vehicle already entered intersection; clear it out

                veh.update_motion(can_move=can_veh_move, lead_vehicle=lead_veh, dt=1.0)

                if veh.crossed and veh not in passed_vehicles and veh.position >= 1.25:
                    passed_vehicles.append(veh)

                # Keep track of wait time
                if veh.speed < 0.5 and not veh.crossed:
                    self.total_wait += 1.0

                lead_veh = veh

        self.total_passed += len(passed_vehicles)
        # Remove cleared vehicles
        self.vehicles = [v for v in self.vehicles if v not in passed_vehicles]

    def _queues(self) -> List[int]:
        return [sum(v.approach == i and not v.crossed for v in self.vehicles) for i in range(4)]

    def get_metrics(self) -> Dict[str, float | int | list]:
        queues = self._queues()
        total_vehicles = len(self.vehicles) + self.total_passed
        active_emergencies = sum(1 for v in self.vehicles if v.emergency and not v.crossed)
        return {
            "time": self.time,
            "queues": queues,
            "total_vehicles": total_vehicles,
            "waiting": len([v for v in self.vehicles if not v.crossed]),
            "passed": self.total_passed,
            "average_wait": self.total_wait / max(1, total_vehicles),
            "average_queue": float(np.mean(queues)),
            "max_queue": max(queues, default=0),
            "efficiency": (self.total_passed / max(1, total_vehicles)) * 100,
            "phase": self.signal_controller.current_phase,
            "phase_name": self.signal_controller.phase_name,
            "episode_reward": self.episode_reward,
            "active_emergencies": active_emergencies,
            "emergency_priority": self.signal_controller.preemption_active,
        }
