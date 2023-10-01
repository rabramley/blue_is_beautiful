from __future__ import annotations
import logging
import threading
import time

from midi.connectors import Midi
from mido import Message


class ClockWatcher():
    def tick(self, tick):
        pass

    def restart(self):
        pass

    def start(self):
        pass

    def stop(self):
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

        for w in self._watchers:
            w.start()

    def cease(self):
        self._tick = 0
        self._running = False

        for w in self._watchers:
            w.stop()

    def toggle(self):
        if self._running:
            self.cease()
        else:
            self.commence()

    def tick(self):
        if not self._running:
            return

        logging.debug('Clock ticking')

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

        for w in self._watchers:
            w.stop()


class MidiClockSender(ClockWatcher):
    def __init__(self, port_name: str, midi_queue: Midi, clock: Clock):
        self.port_name = port_name
        self._midi_queue = midi_queue
        clock.attach_watcher(self)
        self._pulses_per_16th = Clock.PPQN / 4

    def tick(self, tick):

        if tick % self._pulses_per_16th == 0:
            self._midi_queue.queue_message(self.port_name, Message('songpos', pos=int(tick // self._pulses_per_16th)))

        self._midi_queue.queue_message(self.port_name, Message('clock'))

    def restart(self):
        self._midi_queue.queue_message(self.port_name, Message('reset'))

    def start(self):
        self._midi_queue.queue_message(self.port_name, Message('start'))

    def stop(self):
        self._midi_queue.queue_message(self.port_name, Message('stop'))
