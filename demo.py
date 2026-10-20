from __future__ import annotations

import argparse
from pathlib import Path

from smart_traffic_ai.agents import QLearningAgent
from smart_traffic_ai.services import ExperimentRunner


def main():
    parser = argparse.ArgumentParser(description="Run a reproducible Smart Traffic AI demonstration.")
    parser.add_argument("--episodes", type=int, default=25)
    parser.add_argument("--duration", type=int, default=300)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    runner = ExperimentRunner(duration=args.duration, seed=args.seed)
    agent = QLearningAgent(seed=args.seed)
    rewards = runner.train(agent, episodes=args.episodes)
    comparison = runner.compare(agent)
    results = [comparison["baseline"], comparison["rl"]]
    output = Path("data") / "demo_results.csv"
    runner.export_csv(results, output)

    print(f"Training episodes: {len(rewards)}")
    print(f"Learned Q-table states: {len(agent.q_table)}")
    for result in results:
        print(
            f"{result.controller}: average_wait={result.average_wait:.2f}s, "
            f"average_queue={result.average_queue:.2f}, passed={result.passed}, "
            f"throughput={result.throughput_per_minute:.2f}/min"
        )
    print(f"Waiting-time improvement: {comparison['waiting_time_improvement']:.2f}%")
    print(f"CSV results: {output}")


if __name__ == "__main__":
    main()
