from __future__ import annotations

from typing import Any, Dict, Tuple
from smart_traffic_ai.agents.q_learning_agent import QLearningAgent


class RLController:
    """
    Reinforcement learning controller that bridges the Q-learning agent with the simulation.
    """

    def __init__(self, agent: QLearningAgent):
        self.agent = agent

    def select_action(self, state: tuple, explore: bool = True) -> int:
        return self.agent.choose_action(state, explore=explore)

    def explain_decision(self, state: tuple, action: int, queues: list[int], phase: int) -> str:
        """
        Generates a transparent, real factual explanation of the selected action
        based on the actual observed queue sizes and current phase.
        """
        ns_queue = queues[0] + queues[1]
        ew_queue = queues[2] + queues[3]
        action_names = {
            0: "Prioritize North-South Corridor (Action 0)",
            1: "Prioritize East-West Corridor (Action 1)",
            2: "Extend Active Phase Duration (Action 2)",
        }
        chosen = action_names.get(action, f"Action {action}")

        if action == 0:
            if ns_queue >= ew_queue:
                reason = f"North-South queue ({ns_queue} vehicles) exceeds East-West ({ew_queue} vehicles). Switched or maintained NS green to maximize throughput."
            else:
                reason = f"Agent selected NS priority ({ns_queue} vs {ew_queue} vehicles) according to learned policy value."
        elif action == 1:
            if ew_queue >= ns_queue:
                reason = f"East-West queue ({ew_queue} vehicles) exceeds North-South ({ns_queue} vehicles). Prioritizing EW corridor to discharge waiting vehicles."
            else:
                reason = f"Agent selected EW priority ({ew_queue} vs {ns_queue} vehicles) to balance corridor delay."
        else:  # action == 2
            current_corridor = "North-South" if phase in (0, 1) else "East-West"
            reason = f"Extended current {current_corridor} green phase to sustain momentum and reduce switching penalty."

        return f"{chosen}: {reason}"
