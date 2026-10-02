import asyncio
import logging


logger = logging.getLogger(__name__)


async def run_forever(func, interval, stop_event=None, max_iterations=None):
    """
    Запускает async func() каждые interval секунд.

    func           — async-функция без аргументов
    interval       — пауза между вызовами в секундах
    stop_event     — asyncio.Event для graceful shutdown
    max_iterations — если задано, остановиться после N вызовов (для тестов)

    Возвращает число выполненных итераций.
    """
    if stop_event is None:
        stop_event = asyncio.Event()

    iterations = 0
    logger.info("Scheduler started (interval=%s s)", interval)

    while not stop_event.is_set():
        try:
            await func()
        except Exception:
            logger.exception("Error in scheduled task")

        iterations += 1

        if max_iterations is not None and iterations >= max_iterations:
            break

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval)
            break  # stop_event был установлен
        except asyncio.TimeoutError:
            pass  # таймаут истёк, продолжаем

    logger.info("Scheduler stopped after %d iteration(s)", iterations)
    return iterations