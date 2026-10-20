import pytest
from smart_traffic_ai.environment.traffic_environment import TrafficEnvironment
from smart_traffic_ai.controllers.signal_controller import (
    SignalSafetyController,
    PHASE_NS_GREEN,
    PHASE_NS_YELLOW,
    PHASE_EW_GREEN,
    PHASE_EW_YELLOW,
)


def test_emergency_vehicle_types_and_priority():
    """Verify emergency vehicles spawn with emergency attributes and trigger preemption."""
    env = TrafficEnvironment(seed=42, control_interval=1)
    env.request_emergency(approach=2, vehicle_type="ambulance")
    assert env.signal_controller.preemption_active is True
    assert env.emergency_approach == 2

    active_evs = [v for v in env.vehicles if v.emergency]
    assert len(active_evs) == 1
    assert active_evs[0].vehicle_type == "ambulance"
    assert active_evs[0].emergency is True


def test_emergency_preemption_cycles_safely_through_yellow():
    """Verify that an emergency vehicle request on a red approach safely transitions through yellow."""
    controller = SignalSafetyController(min_green=5, yellow_duration=2)
    controller.current_phase = PHASE_NS_GREEN
    controller.phase_time = 6

    # Emergency on East approach (2) - conflicting corridor
    controller.request_emergency_priority(2)

    # Process action: should initiate yellow transition, NOT jump directly to green
    new_phase, reason = controller.request_action(0)
    assert new_phase == PHASE_NS_YELLOW
    assert "yellow" in reason.lower()

    # Complete yellow duration
    controller.tick(2)
    # Controller safely opens EW_GREEN for the emergency corridor
    assert controller.current_phase == PHASE_EW_GREEN
    assert controller.allows_approach(2)


def test_conflicting_emergency_requests_safe_resolution():
    """
    Verify that when multiple emergency vehicles approach from conflicting directions
    (e.g., North and East), the safety controller serves them sequentially without conflicting greens.
    """
    controller = SignalSafetyController(yellow_duration=2)
    controller.reset(initial_phase=PHASE_NS_GREEN)

    # Request North (0) and East (2) simultaneously
    controller.request_emergency_priority(0)
    controller.request_emergency_priority(2)

    # First request (North) is served first
    assert controller.emergency_queue[0] == 0
    assert controller.allows_approach(0)
    assert not controller.allows_approach(2)  # East is still red, no conflict!

    # Clear North after passage
    controller.clear_emergency(0)
    assert controller.emergency_queue[0] == 2  # East is now lead request

    # Controller transitions East through yellow safely
    new_phase, _ = controller.request_action(0)
    assert new_phase == PHASE_NS_YELLOW
    controller.tick(2)
    assert controller.current_phase == PHASE_EW_GREEN
    assert controller.allows_approach(2)
