import pytest
from pathlib import Path
from smart_traffic_ai.agents.q_learning_agent import QLearningAgent
from smart_traffic_ai.environment.vehicle import Vehicle
from smart_traffic_ai.services.experiments import ExperimentResult, ExperimentRunner
from smart_traffic_ai.services.metrics_service import MetricsService


def test_fairness_metric_and_starvation_detection():
    service = MetricsService(starvation_threshold=30.0)
    vehicles = [
        Vehicle(id=1, approach=0, wait_time=10.0),
        Vehicle(id=2, approach=0, wait_time=12.0),
        Vehicle(id=3, approach=2, wait_time=45.0),  # Exceeds 30.0 threshold
    ]
    queues = [2, 0, 1, 0]
    fairness = service.compute_fairness(vehicles, queues)

    assert fairness.max_individual_wait == 45.0
    assert fairness.longest_waiting_approach == 2
    assert fairness.longest_waiting_approach_name == "East"
    assert fairness.is_starved is True
    assert 2 in fairness.starved_approaches


def test_experiment_runner_comparison_and_improvement_formula():
    runner = ExperimentRunner(duration=50, seed=42)
    agent = QLearningAgent(seed=42)
    comparison = runner.compare(agent, duration=50, seed=42)

    assert "baseline" in comparison
    assert "rl" in comparison
    assert "waiting_time_improvement" in comparison
    assert isinstance(comparison["waiting_time_improvement"], float)


def test_division_by_zero_handling():
    # If baseline average wait is 0.0, improvement should be 0.0 rather than ZeroDivisionError
    res_b = ExperimentResult("fixed-time", seed=1, duration=50, average_wait=0.0, average_queue=0.0, max_queue=0, passed=0, waiting=0, throughput_per_minute=0.0, reward=0.0)
    res_rl = ExperimentResult("q-learning", seed=1, duration=50, average_wait=0.0, average_queue=0.0, max_queue=0, passed=0, waiting=0, throughput_per_minute=0.0, reward=0.0)

    imp = ((res_b.average_wait - res_rl.average_wait) / res_b.average_wait * 100) if res_b.average_wait else 0.0
    assert imp == 0.0


def test_csv_export(tmp_path: Path):
    runner = ExperimentRunner(duration=40, seed=42)
    results = [
        ExperimentResult("fixed-time", seed=42, duration=40, average_wait=12.5, average_queue=3.2, max_queue=7, passed=24, waiting=4, throughput_per_minute=36.0, reward=-15.0),
        ExperimentResult("q-learning", seed=42, duration=40, average_wait=8.2, average_queue=2.1, max_queue=5, passed=30, waiting=2, throughput_per_minute=45.0, reward=25.0),
    ]
    csv_file = tmp_path / "test_results.csv"
    runner.export_csv(results, csv_file)

    assert csv_file.exists()
    content = csv_file.read_text(encoding="utf-8")
    assert "fixed-time" in content
    assert "q-learning" in content
    assert "12.5" in content
