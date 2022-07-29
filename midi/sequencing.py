from __future__ import annotations
from dataclasses import dataclass
from mido import Message
from midi.clock import Clock, ClockWatcher
from midi.connections import MessageSource
from itertools import cycle
from midi.connectors import Midi
import random
import logging
from sortedcontainers import SortedList


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


@dataclass
class Note():
    note: int
    velocity: int
    tick_off: int


class NoteSource():
    def __init__(self, denominator: int, pattern: str):
        self._pulses_per_beat = Clock.PPQN * 4 / denominator
        self._gate_length = self._pulses_per_beat
        self._pattern = pattern
        self._denominator = denominator

    def get_notes(self, tick):
        if tick % self._pulses_per_beat > 0:
            return []

        beat = int((tick // self._pulses_per_beat) % self._denominator)

        result = []

        if self._pattern[beat] =='x':
            note = (random.randint(35, 39) * 2)
            result.append(Note(note=note, velocity=100, tick_off=int(tick + self._gate_length * 3)))
        
        return result


class SequencerTrack(ClockWatcher, MessageSource):
    def __init__(self, clock: Clock, source: NoteSource):
        super().__init__()

        self._note_source = source
        self._notes_off = SortedList(key=lambda n: n.tick_off)

        clock.attach_watcher(self)

    def tick(self, tick):
        split_point = self._notes_off.bisect_right(Note(note=0, velocity=0, tick_off=tick))

        for o in (self._notes_off.pop(index=0) for _ in range(split_point)):
            self.send_message(Message('note_off', channel=0, note=o.note, velocity=o.velocity, time=0))

        for n in self._note_source.get_notes(tick):
            self.send_message(Message('note_on', channel=0, note=n.note, velocity=n.velocity, time=0))
            self._notes_off.add(n)

    def restart(self):
        pass
