from __future__ import annotations
import logging
from mido import Message
from midi.clock import Clock, ClockWatcher
from midi.connections import MessageSource
from itertools import cycle
from midi.connectors import Midi


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


class SequencerTrack(ClockWatcher, MessageSource):
    def __init__(self, clock: Clock, note: int, velocity: int, denominator: int, pattern: str):
        super().__init__()

        self._note = note
        self._velocity = velocity
        self._connectors = []
        self._pulses_per_beat = Clock.PPQN * 4 / denominator
        self._original_pattern = pattern

        self.restart()
        clock.attach_watcher(self)

    def tick(self, tick):
        if tick % self._pulses_per_beat == 0:
            self.beat()
    
    def beat(self):
        if next(self._pattern) != '.':
            self.send_message(Message('note_on', channel=0, note=self._note, velocity=self._velocity, time=0))

    def restart(self):
        self._pattern = cycle(self._original_pattern)
