import asyncio

from app.scheduler import run_forever


async def test_scheduler_calls_func_n_times():
    calls = []

    async def task():
        calls.append(1)

    await run_forever(task, interval=0.001, max_iterations=3)
    assert len(calls) == 3


async def test_scheduler_returns_iteration_count():
    async def task():
        pass

    iterations = await run_forever(task, interval=0.001, max_iterations=5)
    assert iterations == 5


async def test_scheduler_stops_on_stop_event():
    stop_event = asyncio.Event()
    stop_event.set()

    calls = []

    async def task():
        calls.append(1)

    await run_forever(task, interval=0.001, stop_event=stop_event)
    assert len(calls) == 0


async def test_scheduler_survives_exception_in_func():
    calls = []

    async def failing():
        calls.append(1)
        raise ValueError("boom")

    await run_forever(failing, interval=0.001, max_iterations=3)
    assert len(calls) == 3