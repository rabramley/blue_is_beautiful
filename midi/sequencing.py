from __future__ import annotations
from mido import Message
from midi.clock import Clock, ClockWatcher
from midi.connections import MessageSource


class SequencerTrack(ClockWatcher, MessageSource):
    def __init__(self, clock: Clock, note: int, velocity: int, denominator: int):
        super().__init__()

        self._note = note
        self._velocity = velocity
        self._connectors = []
        self._pulses_per_beat = Clock.PPQN * 4 / denominator

        clock.attach_watcher(self)

    def tick(self, tick):
        if tick % self._pulses_per_beat == 0:
            self.beat()
    
    def beat(self):
        self.send_message(Message('note_on', channel=0, note=self._note, velocity=self._velocity, time=0))


