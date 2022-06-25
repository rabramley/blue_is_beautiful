from __future__ import annotations
import logging
import time


class ClockWatcher():
    def tick(self, tick):
        pass


class Clock():
    NANO_SECONDS_PER_MINUTE = 60_000_000_000
    PPQN = 24

    def __init__(self, bpm: int):
        self._interval = int(Clock.NANO_SECONDS_PER_MINUTE / bpm / Clock.PPQN)
        self._tick = 0
        self._running = False
        self._watchers = []
        self._next = 0
    
    def attach_watcher(self, watcher: ClockWatcher):
        self._watchers.append(watcher)

    def start(self):
        self._tick = 0
        self._next = time.monotonic_ns()
        self._running = True

    def stop(self):
        self._tick = 0
        self._running = False

    def toggle(self):
        if self._running:
            self.stop()
        else:
            self.start()

    def tick(self):
        if not self._running:
            return

        if self._next < time.monotonic_ns():
            for w in self._watchers:
                w.tick(self._tick)

            self._tick += 1
            self._next += self._interval
