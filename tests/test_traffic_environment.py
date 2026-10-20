import pytest
from smart_traffic_ai.environment.traffic_environment import TrafficEnvironment
from smart_traffic_ai.environment.vehicle import Vehicle


def test_vehicle_generation_across_all_approaches():
    """Verify vehicles generate across all four approaches (North, South, East, West)."""
    # High arrival rates to guarantee vehicle arrivals on all approaches
    env = TrafficEnvironment(arrival_rates=(0.9, 0.9, 0.9, 0.9), seed=42)
    env.reset(seed=42)
    # Step a few seconds
    for _ in range(5):
        env.step(0)
    queues = env._queues()
    assert all(q > 0 for q in queues), f"Expected vehicles on all 4 approaches, got {queues}"


def test_vehicle_stopping_at_red_signal():
    """Verify vehicles stop safely before red signals and do not cross stop line."""
    env = TrafficEnvironment(seed=42, control_interval=1)
    # Force phase to NS_GREEN (phase 0). Approaches 2 (East) and 3 (West) are RED.
    env.phase = 0
    # Add a vehicle on East approach (2)
    v = Vehicle(id=999, approach=2, position=0.5)
    env.vehicles.append(v)

    # Step simulation
    for _ in range(10):
        env._move_one_second()

    # East is red, vehicle should not cross stop line (position <= 1.0)
    assert not v.crossed
    assert v.position <= 1.0
    assert v.wait_time > 0


def test_vehicle_crossing_on_green_signal():
    """Verify vehicles accelerate and cross intersection when signal is green."""
    env = TrafficEnvironment(seed=42, control_interval=1)
    # North-South is Green (phase 0)
    env.phase = 0
    v = Vehicle(id=998, approach=0, position=0.8)
    env.vehicles.append(v)

    for _ in range(10):
        env._move_one_second()

    # Vehicle should have crossed and cleared
    assert v.crossed or v not in env.vehicles


def test_state_discretization_buckets():
    """Verify queue lengths are mapped to discrete categories: Low (0-4), Med (5-9), High (10+)."""
    env = TrafficEnvironment(seed=42)
    # 2 vehicles on North, 6 on South, 12 on East, 0 on West
    env.vehicles = (
        [Vehicle(id=i, approach=0) for i in range(2)]
        + [Vehicle(id=10 + i, approach=1) for i in range(6)]
        + [Vehicle(id=20 + i, approach=2) for i in range(12)]
    )
    state = env.get_state()
    # State format: (N_bucket, S_bucket, E_bucket, W_bucket, phase)
    assert state[0] == 0  # 2 vehicles -> Low (0)
    assert state[1] == 1  # 6 vehicles -> Med (1)
    assert state[2] == 2  # 12 vehicles -> High (2)
    assert state[3] == 0  # 0 vehicles -> Low (0)


def test_empty_traffic_conditions():
    """Verify simulation handles zero traffic gracefully without errors."""
    env = TrafficEnvironment(arrival_rates=(0.0, 0.0, 0.0, 0.0), seed=42)
    state, metrics = env.reset()
    assert metrics["waiting"] == 0
    assert metrics["passed"] == 0

    for _ in range(10):
        state, reward, done, info = env.step(0)
    assert metrics["waiting"] == 0
    assert not done


def test_high_density_traffic_conditions():
    """Verify simulation remains stable and bounds queues safely during peak congestion."""
    env = TrafficEnvironment(arrival_rates=(0.8, 0.8, 0.8, 0.8), seed=42)
    env.reset()
    for _ in range(20):
        state, reward, done, info = env.step(0 if _ % 2 == 0 else 1)
    metrics = env.get_metrics()
    assert metrics["total_vehicles"] > 10
    assert metrics["average_queue"] > 0
