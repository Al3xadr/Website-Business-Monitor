import logging
import threading


logger = logging.getLogger(__name__)


def run_forever(func, interval, stop_event=None, max_iterations=None):
    """
    Запускает func() каждые interval секунд.
    """
    if stop_event is None:
        stop_event = threading.Event()

    iterations = 0
    logger.info("Scheduler started (interval=%s s)", interval)

    while not stop_event.is_set():
        try:
            func()
        except Exception:
            logger.exception("Error in scheduled task")

        iterations += 1   # ← вынесли ЗА пределы try/except

        if max_iterations is not None and iterations >= max_iterations:
            break

        if stop_event.wait(timeout=interval):
            break

    logger.info("Scheduler stopped after %d iteration(s)", iterations)
    return iterations