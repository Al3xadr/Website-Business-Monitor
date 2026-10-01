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

def test_sequence_up_up_up_no_events():
    """UP → UP → UP — ни одного события."""
    tracker = StateTracker()
    events = []

    for status in ["UP", "UP", "UP"]:
        changed, previous = tracker.update(status)
        if changed:
            events.append((previous, status))

    # Первое UP — событие (None → UP), дальше тишина
    assert events == [(None, "UP")]


def test_sequence_up_down_no_new_events():
    """UP → DOWN → DOWN — одно событие падения, второе DOWN не считается."""
    tracker = StateTracker()
    events = []

    for status in ["UP", "DOWN", "DOWN"]:
        changed, previous = tracker.update(status)
        if changed:
            events.append((previous, status))

    assert events == [(None, "UP"), ("UP", "DOWN")]


def test_sequence_down_up_no_new_events():
    """DOWN → UP — одно событие восстановления."""
    tracker = StateTracker()
    events = []

    for status in ["DOWN", "UP"]:
        changed, previous = tracker.update(status)
        if changed:
            events.append((previous, status))

    assert events == [(None, "DOWN"), ("DOWN", "UP")]


def test_sequence_full_cycle():
    """Полный цикл: UP → UP → DOWN → DOWN → UP → UP."""
    tracker = StateTracker()
    events = []

    for status in ["UP", "UP", "DOWN", "DOWN", "UP", "UP"]:
        changed, previous = tracker.update(status)
        if changed:
            events.append((previous, status))

    assert events == [
        (None, "UP"),         # первый запуск
        ("UP", "DOWN"),       # упал
        ("DOWN", "UP"),       # восстановился
    ]