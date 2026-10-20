from __future__ import annotations

import json
from pathlib import Path
import random
from typing import Dict, List, Optional, Tuple


class QLearningAgent:
    """
    Genuine Tabular Q-Learning Agent implemented from scratch.
    Learns state-action values Q(s, a) using the Bellman optimality update:
    Q(s, a) = Q(s, a) + alpha * [reward + gamma * max_a' Q(s', a') - Q(s, a)]
    """

    def __init__(
        self,
        alpha: float = 0.15,
        gamma: float = 0.92,
        epsilon: float = 1.0,
        epsilon_min: float = 0.05,
        decay: float = 0.995,
        seed: int | None = None,
    ):
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.initial_epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.decay = decay
        self.rng = random.Random(seed)
        self.q_table: dict[str, list[float]] = {}
        self.visit_counts: dict[str, int] = {}

    @property
    def is_trained(self) -> bool:
        """Returns True if the agent has learned non-zero Q-values."""
        if not self.q_table:
            return False
        return any(any(val != 0.0 for val in values) for values in self.q_table.values())

    @staticmethod
    def key(state) -> str:
        return ",".join(map(str, state))

    def values(self, state) -> list[float]:
        k = self.key(state)
        return self.q_table.setdefault(k, [0.0, 0.0, 0.0])

    def choose_action(self, state, explore: bool = True) -> int:
        """
        Epsilon-greedy action selection:
        With probability epsilon, select random action (exploration);
        otherwise select action with maximum Q-value (exploitation).
        """
        values = self.values(state)
        k = self.key(state)
        self.visit_counts[k] = self.visit_counts.get(k, 0) + 1

        if explore and self.rng.random() < self.epsilon:
            return self.rng.randrange(3)
        return max(range(3), key=lambda action: values[action])

    def update(self, state, action: int, reward: float, next_state, done: bool = False) -> float:
        """
        Applies tabular Q-learning update equation.
        Returns the TD error (temporal difference error).
        """
        current_values = self.values(state)
        next_best = 0.0 if done else max(self.values(next_state))
        target = reward + self.gamma * next_best
        td_error = target - current_values[action]
        current_values[action] += self.alpha * td_error
        return td_error

    def end_episode(self) -> None:
        """Decays exploration rate epsilon at the completion of an episode."""
        self.epsilon = max(self.epsilon_min, self.epsilon * self.decay)

    def reset_training(self) -> None:
        self.q_table.clear()
        self.visit_counts.clear()
        self.epsilon = self.initial_epsilon

    def get_top_states(self, limit: int = 15) -> List[Tuple[str, List[float], int, int]]:
        """
        Returns list of (state_key, q_values, best_action, visit_count)
        sorted by visit count descending.
        """
        items = []
        for state_key, values in self.q_table.items():
            visits = self.visit_counts.get(state_key, 1)
            best_act = max(range(3), key=lambda a: values[a])
            items.append((state_key, values, best_act, visits))
        items.sort(key=lambda x: x[3], reverse=True)
        return items[:limit]

    def save(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "hyperparameters": {
                "alpha": self.alpha,
                "gamma": self.gamma,
                "epsilon": self.epsilon,
                "epsilon_min": self.epsilon_min,
                "decay": self.decay,
            },
            "q_table": self.q_table,
            "visit_counts": self.visit_counts,
        }
        target.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def load(self, path: str | Path) -> bool:
        source = Path(path)
        if not source.exists():
            return False
        try:
            data = json.loads(source.read_text(encoding="utf-8"))
            if "q_table" in data:
                self.q_table = data["q_table"]
                self.visit_counts = data.get("visit_counts", {})
                params = data.get("hyperparameters", {})
                self.alpha = params.get("alpha", self.alpha)
                self.gamma = params.get("gamma", self.gamma)
                self.epsilon = params.get("epsilon", self.epsilon)
            else:
                # Raw Q-table dict fallback
                self.q_table = data
            return True
        except Exception as e:
            print(f"Error loading Q-table: {e}")
            return False
