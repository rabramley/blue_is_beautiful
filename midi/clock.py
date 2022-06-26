from __future__ import annotations
import threading
import time


class ClockWatcher():
    def tick(self, tick):
        pass

    def restart(self):
        pass


class Clock(threading.Thread):
    NANO_SECONDS_PER_MINUTE = 60_000_000_000
    PPQN = 24

    def __init__(self, bpm: int):
        super().__init__()

        self._interval = int(Clock.NANO_SECONDS_PER_MINUTE / bpm / Clock.PPQN)
        self._tick = 0
        self._running = False
        self._watchers = []
        self._next = 0
        self._done = False
    
    def attach_watcher(self, watcher: ClockWatcher):
        self._watchers.append(watcher)

    def commence(self):
        for w in self._watchers:
            w.restart()

        self._tick = 0
        self._next = time.monotonic_ns()
        self._running = True

    def cease(self):
        self._tick = 0
        self._running = False

    def toggle(self):
        if self._running:
            self.cease()
        else:
            self.commence()

    def tick(self):
        if not self._running:
            return

        if self._next < time.monotonic_ns():
            for w in self._watchers:
                w.tick(self._tick)

            self._tick += 1
            self._next += self._interval

    def run(self):
        while not self._done:
            self.tick()
            time.sleep(0.0000001)

    def stop(self):
        self._done = True


