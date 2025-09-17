import time

class GameTimer:
    def __init__(self):
        self._start = None
        self._elapsed = 0.0
        self._running = False

    def start(self):
        if not self._running:
            self._running = True
            self._start = time.perf_counter()

    def stop(self):
        if self._running:
            self._elapsed += time.perf_counter() - self._start
            self._running = False
            self._start = None

    def reset(self):
        self._start = None
        self._elapsed = 0.0
        self._running = False

    def seconds(self):
        if self._running and self._start is not None:
            return int(self._elapsed + (time.perf_counter() - self._start))
        return int(self._elapsed)
