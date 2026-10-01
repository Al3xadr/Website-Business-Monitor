from app.scheduler import run_forever


def test_scheduler_calls_func_n_times():
    calls = []
    run_forever(lambda: calls.append(1), interval=0, max_iterations=3)
    assert len(calls) == 3


def test_scheduler_returns_iteration_count():
    iterations = run_forever(lambda: None, interval=0, max_iterations=5)
    assert iterations == 5


def test_scheduler_stops_on_stop_event():
    import threading
    stop_event = threading.Event()
    stop_event.set()  # уже установлен — цикл не должен даже начаться

    calls = []
    run_forever(lambda: calls.append(1), interval=0, stop_event=stop_event)
    assert len(calls) == 0


def test_scheduler_survives_exception_in_func():
    calls = []

    def failing():
        calls.append(1)
        raise ValueError("boom")

    run_forever(failing, interval=0, max_iterations=3)
    assert len(calls) == 3  # несмотря на исключения — все 3 итерации прошли