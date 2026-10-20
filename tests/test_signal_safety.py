import pytest
from smart_traffic_ai.controllers.signal_controller import (
    SignalSafetyController,
    PHASE_NS_GREEN,
    PHASE_NS_YELLOW,
    PHASE_EW_GREEN,
    PHASE_EW_YELLOW,
)


def test_no_conflicting_green_phases():
    """Verify that North-South green and East-West green can never occur simultaneously."""
    controller = SignalSafetyController()
    for _ in range(100):
        assert controller.current_phase in (PHASE_NS_GREEN, PHASE_NS_YELLOW, PHASE_EW_GREEN, PHASE_EW_YELLOW)
        # In mutually exclusive phases, if NS green is active, EW is red
        green_approaches = controller.get_green_approaches()
        if controller.current_phase == PHASE_NS_GREEN:
            assert green_approaches == (0, 1)
            assert not controller.allows_approach(2)
            assert not controller.allows_approach(3)
        elif controller.current_phase == PHASE_EW_GREEN:
            assert green_approaches == (2, 3)
            assert not controller.allows_approach(0)
            assert not controller.allows_approach(1)
        controller.tick(1)


def test_transition_must_go_through_yellow():
    """Verify that moving between conflicting corridors requires yellow clearance."""
    controller = SignalSafetyController(min_green=5, yellow_duration=2)
    controller.current_phase = PHASE_NS_GREEN
    controller.phase_time = 6  # min green satisfied

    # Request switch to EW
    new_phase, reason = controller.request_action(1)
    # Must switch to NS_YELLOW first, NOT directly to EW_GREEN
    assert new_phase == PHASE_NS_YELLOW
    assert controller.current_phase == PHASE_NS_YELLOW

    # Advance 1 second: should remain yellow
    controller.tick(1)
    assert controller.current_phase == PHASE_NS_YELLOW

    # Advance 1 second: yellow duration (2s) completed, transitions to EW_GREEN
    controller.tick(1)
    assert controller.current_phase == PHASE_EW_GREEN


def test_minimum_green_enforcement():
    """Verify that minimum green duration is enforced before corridor switch is allowed."""
    controller = SignalSafetyController(min_green=10, yellow_duration=2)
    controller.current_phase = PHASE_NS_GREEN
    controller.phase_time = 3  # Less than min_green

    new_phase, reason = controller.request_action(1)
    # Request rejected/deferred: remains NS_GREEN
    assert new_phase == PHASE_NS_GREEN
    assert "minimum green" in reason.lower()


def test_maximum_green_enforcement():
    """Verify that maximum green forces transition to yellow to prevent starvation."""
    controller = SignalSafetyController(min_green=5, max_green=20, yellow_duration=2)
    controller.current_phase = PHASE_NS_GREEN
    controller.phase_time = 20

    new_phase, reason = controller.request_action(2)  # Request extension
    assert new_phase == PHASE_NS_YELLOW
    assert "max green" in reason.lower()
