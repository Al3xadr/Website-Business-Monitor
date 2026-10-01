import logging


logger = logging.getLogger(__name__)


class StateTracker:
    """Хранит предыдущее состояние и говорит, изменилось ли оно."""

    def __init__(self):
        self.previous = None

    def update(self, current):
        """
        Обновляет состояние.
        Возвращает True, если состояние изменилось.
        """
        changed = current != self.previous
        old = self.previous
        self.previous = current
        return changed, old