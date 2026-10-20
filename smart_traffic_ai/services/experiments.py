from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional

from smart_traffic_ai.agents.q_learning_agent import QLearningAgent


@dataclass
class ExperimentResult:
    controller: str
    seed: int
    duration: int
    average_wait: float
    average_queue: float
    max_queue: int
    passed: int
    waiting: int
    throughput_per_minute: float
    reward: float
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class ExperimentRunner:
    """Runs reproducible baseline, training, evaluation, and comparison experiments."""

    def __init__(
        self,
        arrival_rates: tuple[float, float, float, float] | list[float] | None = None,
        duration: int = 300,
        seed: int = 42,
    ):
        self.arrival_rates = list(arrival_rates or (0.22, 0.20, 0.18, 0.16))
        self.duration = duration
        self.seed = seed

    def run_fixed_time(self, duration: int | None = None, seed: int | None = None) -> ExperimentResult:
        from smart_traffic_ai.environment.traffic_environment import TrafficEnvironment
        run_duration = duration or self.duration
        run_seed = seed if seed is not None else self.seed

        env = TrafficEnvironment(seed=run_seed, arrival_rates=self.arrival_rates)
        state, _ = env.reset(seed=run_seed)

        while env.time < run_duration:
            # Fixed time cycle: 20 seconds NS green, 20 seconds EW green
            action = 0 if (env.time // 20) % 2 == 0 else 1
            state, _, done, _ = env.step(action)
            if done:
                break

        return self._result("fixed-time", env)

    def train(
        self,
        agent: QLearningAgent,
        episodes: int = 25,
        progress_callback: Optional[Callable[[int, int, float], None]] = None,
    ) -> List[float]:
        from smart_traffic_ai.environment.traffic_environment import TrafficEnvironment
        rewards = []
        for episode in range(episodes):
            ep_seed = self.seed + episode
            env = TrafficEnvironment(seed=ep_seed, arrival_rates=self.arrival_rates)
            state, _ = env.reset(seed=ep_seed)
            done = False
            total_reward = 0.0

            while not done:
                action = agent.choose_action(state, explore=True)
                next_state, reward, done, _ = env.step(action)
                agent.update(state, action, reward, next_state, done)
                state = next_state
                total_reward += reward

            agent.end_episode()
            rewards.append(total_reward)

            if progress_callback:
                progress_callback(episode + 1, episodes, total_reward)

        return rewards

    def run_rl(
        self,
        agent: QLearningAgent,
        duration: int | None = None,
        seed: int | None = None,
    ) -> ExperimentResult:
        from smart_traffic_ai.environment.traffic_environment import TrafficEnvironment
        run_duration = duration or self.duration
        run_seed = seed if seed is not None else self.seed

        env = TrafficEnvironment(seed=run_seed, arrival_rates=self.arrival_rates)
        state, _ = env.reset(seed=run_seed)

        while env.time < run_duration:
            # Pure evaluation mode: exploration disabled
            action = agent.choose_action(state, explore=False)
            state, _, done, _ = env.step(action)
            if done:
                break

        return self._result("q-learning", env)

    def compare(
        self,
        agent: QLearningAgent,
        duration: int | None = None,
        seed: int | None = None,
    ) -> Dict[str, Any]:
        """Runs identical baseline and RL trials under identical traffic arrival conditions."""
        baseline = self.run_fixed_time(duration=duration, seed=seed)
        rl = self.run_rl(agent, duration=duration, seed=seed)

        if baseline.average_wait > 0:
            improvement = ((baseline.average_wait - rl.average_wait) / baseline.average_wait) * 100.0
        else:
            improvement = 0.0

        throughput_gain = rl.throughput_per_minute - baseline.throughput_per_minute

        return {
            "baseline": baseline,
            "rl": rl,
            "waiting_time_improvement": improvement,
            "throughput_gain": throughput_gain,
            "seed": seed if seed is not None else self.seed,
            "duration": duration or self.duration,
        }

    def export_csv(self, results: List[ExperimentResult], path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        if not results:
            return
        fieldnames = list(asdict(results[0]).keys())
        with target.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for res in results:
                writer.writerow(asdict(res))

    @staticmethod
    def _result(controller: str, env: Any) -> ExperimentResult:
        metrics = env.get_metrics()
        return ExperimentResult(
            controller=controller,
            seed=env.seed or 0,
            duration=env.time,
            average_wait=float(metrics["average_wait"]),
            average_queue=float(metrics["average_queue"]),
            max_queue=int(metrics["max_queue"]),
            passed=int(metrics["passed"]),
            waiting=int(metrics["waiting"]),
            throughput_per_minute=float(metrics["passed"]) / max(1, env.time) * 60.0,
            reward=float(metrics["episode_reward"]),
        )
