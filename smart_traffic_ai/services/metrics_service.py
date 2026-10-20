from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import numpy as np


@dataclass
class RewardBreakdown:
    pass_reward: float = 0.0
    wait_penalty: float = 0.0
    queue_penalty: float = 0.0
    switch_penalty: float = 0.0
    starvation_penalty: float = 0.0
    total_reward: float = 0.0


@dataclass
class FairnessMetrics:
    max_individual_wait: float = 0.0
    longest_waiting_approach: int = 0
    longest_waiting_approach_name: str = "North"
    approach_wait_variance: float = 0.0
    starved_approaches: List[int] = field(default_factory=list)
    is_starved: bool = False


class MetricsService:
    """
    Centralized service for tracking real-time simulation metrics, fairness, and history buffers.
    """

    def __init__(self, starvation_threshold: float = 40.0):
        self.starvation_threshold = starvation_threshold
        self.reset()

    def reset(self) -> None:
        self.history_time: List[int] = []
        self.history_queues: List[List[int]] = []
        self.history_avg_wait: List[float] = []
        self.history_passed: List[int] = []
        self.history_rewards: List[float] = []
        self.latest_reward_breakdown = RewardBreakdown()
        self.latest_fairness = FairnessMetrics()

    def compute_fairness(self, vehicles: list, queues: list[int]) -> FairnessMetrics:
        approach_names = ("North", "South", "East", "West")
        approach_waits = [0.0, 0.0, 0.0, 0.0]
        approach_counts = [0, 0, 0, 0]
        max_indiv_wait = 0.0

        for v in vehicles:
            if not v.crossed:
                approach_waits[v.approach] += v.wait_time
                approach_counts[v.approach] += 1
                if v.wait_time > max_indiv_wait:
                    max_indiv_wait = v.wait_time

        avg_waits_per_approach = [
            approach_waits[i] / max(1, approach_counts[i]) for i in range(4)
        ]

        longest_idx = int(np.argmax(avg_waits_per_approach))
        wait_var = float(np.var(avg_waits_per_approach))

        starved = [
            i for i, wait in enumerate(avg_waits_per_approach)
            if wait >= self.starvation_threshold and queues[i] > 0
        ]

        fairness = FairnessMetrics(
            max_individual_wait=max_indiv_wait,
            longest_waiting_approach=longest_idx,
            longest_waiting_approach_name=approach_names[longest_idx],
            approach_wait_variance=wait_var,
            starved_approaches=starved,
            is_starved=len(starved) > 0,
        )
        self.latest_fairness = fairness
        return fairness

    def record_step(
        self,
        time_step: int,
        queues: list[int],
        avg_wait: float,
        passed_count: int,
        reward: float,
        breakdown: RewardBreakdown | None = None,
    ) -> None:
        self.history_time.append(time_step)
        self.history_queues.append(list(queues))
        self.history_avg_wait.append(avg_wait)
        self.history_passed.append(passed_count)
        self.history_rewards.append(reward)
        if breakdown:
            self.latest_reward_breakdown = breakdown

        # Limit buffer length to prevent memory leaks in long-running desktop app
        if len(self.history_time) > 2000:
            self.history_time.pop(0)
            self.history_queues.pop(0)
            self.history_avg_wait.pop(0)
            self.history_passed.pop(0)
            self.history_rewards.pop(0)
