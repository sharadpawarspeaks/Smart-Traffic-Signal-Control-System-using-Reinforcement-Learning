import pytest
from pathlib import Path
from smart_traffic_ai.agents.q_learning_agent import QLearningAgent


def test_q_table_initialization_and_untrained_state():
    agent = QLearningAgent(seed=42)
    assert not agent.is_trained
    assert len(agent.q_table) == 0


def test_q_learning_update_equation():
    agent = QLearningAgent(alpha=0.2, gamma=0.9, epsilon=0.0, seed=42)
    s1 = (0, 0, 0, 0, 0)
    s2 = (1, 0, 0, 0, 0)

    # Initial Q(s1, 0) is 0.0
    assert agent.values(s1)[0] == 0.0

    # Next state s2 has Q(s2, a) = [0.0, 5.0, 0.0], max Q is 5.0
    agent.values(s2)[1] = 5.0

    # Q(s1, 0) = Q(s1, 0) + alpha * [reward + gamma * max_Q(s2) - Q(s1, 0)]
    # Q(s1, 0) = 0.0 + 0.2 * [10.0 + 0.9 * 5.0 - 0.0] = 0.2 * 14.5 = 2.9
    td_error = agent.update(s1, 0, 10.0, s2, done=False)
    assert pytest.approx(agent.values(s1)[0], 0.001) == 2.9
    assert pytest.approx(td_error, 0.001) == 14.5
    assert agent.is_trained


def test_epsilon_greedy_exploration_and_exploitation():
    # Pure exploitation (epsilon = 0.0)
    agent = QLearningAgent(epsilon=0.0, seed=42)
    s = (1, 1, 0, 0, 0)
    agent.values(s)[1] = 10.0  # Action 1 is strictly best
    assert agent.choose_action(s, explore=True) == 1

    # Pure exploration (epsilon = 1.0)
    agent_explore = QLearningAgent(epsilon=1.0, seed=42)
    actions = {agent_explore.choose_action(s, explore=True) for _ in range(30)}
    assert len(actions) > 1  # Should explore multiple actions


def test_epsilon_decay():
    agent = QLearningAgent(epsilon=1.0, epsilon_min=0.1, decay=0.9, seed=42)
    agent.end_episode()
    assert pytest.approx(agent.epsilon, 0.001) == 0.9
    for _ in range(50):
        agent.end_episode()
    assert agent.epsilon >= 0.1


def test_q_table_persistence(tmp_path: Path):
    agent = QLearningAgent(alpha=0.25, gamma=0.85, seed=42)
    s = (2, 1, 0, 1, 2)
    agent.values(s)[2] = 7.75

    file_path = tmp_path / "test_q.json"
    agent.save(file_path)
    assert file_path.exists()

    agent2 = QLearningAgent(seed=99)
    assert agent2.load(file_path) is True
    assert pytest.approx(agent2.values(s)[2], 0.001) == 7.75
    assert agent2.alpha == 0.25
    assert agent2.gamma == 0.85


def test_top_states_inspector():
    agent = QLearningAgent(seed=42)
    s1, s2 = (0, 0, 0, 0, 0), (1, 2, 0, 1, 0)
    agent.values(s1)[0] = 3.0
    agent.values(s2)[1] = 5.0
    # Simulate visits
    for _ in range(5):
        agent.choose_action(s1, explore=False)
    for _ in range(12):
        agent.choose_action(s2, explore=False)

    top = agent.get_top_states(limit=2)
    assert len(top) == 2
    assert top[0][0] == agent.key(s2)  # s2 has 12 visits
    assert top[0][2] == 1              # best action is 1
