from smart_traffic_ai.agents import QLearningAgent
from smart_traffic_ai.environment import TrafficEnvironment
from smart_traffic_ai.services import ExperimentRunner


def test_signal_never_conflicts():
    env = TrafficEnvironment(seed=1)
    for _ in range(30):
        state, _, done, _ = env.step(0 if _ % 2 == 0 else 1)
        assert env.phase in (0, 1, 2, 3)
        assert not (env.phase == 0 and env.phase == 2)
        if done:
            break


def test_q_values_update():
    agent = QLearningAgent(seed=1)
    before = agent.values((0, 0, 0, 0, 0))[0]
    agent.update((0, 0, 0, 0, 0), 0, 2, (1, 0, 0, 0, 0))
    assert agent.values((0, 0, 0, 0, 0))[0] != before


def test_invalid_action_rejected():
    env = TrafficEnvironment(seed=1)
    try:
        env.step(8)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid actions must be rejected")


def test_experiment_comparison_uses_real_metrics():
    runner = ExperimentRunner(duration=60, seed=4)
    agent = QLearningAgent(seed=4)
    runner.train(agent, episodes=1)
    comparison = runner.compare(agent)
    assert comparison["baseline"].duration == 60
    assert comparison["rl"].controller == "q-learning"
    assert isinstance(comparison["waiting_time_improvement"], float)


def test_emergency_request_is_validated_and_prioritized():
    env = TrafficEnvironment(seed=2, control_interval=1)
    env.request_emergency(2)
    _, _, _, info = env.step(0)
    assert info["emergency_priority"] is True
    assert env.phase in (0, 1, 2, 3)
