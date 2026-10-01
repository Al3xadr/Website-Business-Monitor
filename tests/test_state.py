from app.state import StateTracker


def test_first_update_is_change():
    tracker = StateTracker()
    changed, previous = tracker.update("UP")
    assert changed is True
    assert previous is None


def test_same_state_is_not_change():
    tracker = StateTracker()
    tracker.update("UP")
    changed, previous = tracker.update("UP")
    assert changed is False
    assert previous == "UP"


def test_transition_up_to_down():
    tracker = StateTracker()
    tracker.update("UP")
    changed, previous = tracker.update("DOWN")
    assert changed is True
    assert previous == "UP"


def test_transition_down_to_up():
    tracker = StateTracker()
    tracker.update("DOWN")
    changed, previous = tracker.update("UP")
    assert changed is True
    assert previous == "DOWN"


def test_none_to_down_is_change():
    tracker = StateTracker()
    changed, previous = tracker.update("DOWN")
    assert changed is True
    assert previous is None