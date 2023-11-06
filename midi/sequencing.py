from __future__ import annotations
from dataclasses import dataclass
from mido import Message
from midi.clock import Clock, ClockWatcher
from midi.connections import MessageSource
import random
from sortedcontainers import SortedList
from midi.connectors import PortManager

from midi.scales import Scale


def get_sequencer(clock, config: dict, port_manager: PortManager):
    port = port_manager.get_out_channel(config['port'], config['channel'])
    if config['sequence_type'] == 'drum':
        return NoteDespatcher(
            clock,
            DrumSource(
                config['note_number'],
                config['denominator'],
                config['pattern'],                
                config['velocity'],                
            ),
            port,
        )
    else:
        return NoteDespatcher(
            clock,
            RandomNoteSource(
                _get_note_provider(config['note_provider']),
                config['denominator'],
                config['gate_length'],
                config['pattern'],
                ),
            port,
            )

def _get_note_provider(config):
    return Scale(
        config['key'],
        config['mode'],
        config['lowest_octave'],
        config['highest_octave'],
    )


@dataclass
class Note():
    note: int
    velocity: int
    tick_off: int


class NoteSource():
    def get_notes(self, tick: int) -> list:
        pass


class PatternSymbolDecoder():
    def get_notes(self, symbol: str) -> list:
        pass


class RandomNoteDecoder(PatternSymbolDecoder):
    def __init__(self, scale: Scale):
        self._scale = scale
        self._notes = scale.get_notes()

    def get_notes(self, symbol: str):
        result = []
        
        if symbol =='x':
            note = random.choice(self._notes)
            result.append(Note(note=note, velocity=100, tick_off=int(tick + self._gate_length)))
        
        return result


class PatternReader(NoteSource):
    def __init__(self, denominator: int, pattern: str, symbol_decoder: PatternSymbolDecoder):
        self._pulses_per_beat = Clock.PPQN * 4 / denominator
        self._pattern = pattern
        self._denominator = denominator
        self._symbol_decoder = symbol_decoder

    def get_notes(self, tick):
        if tick % self._pulses_per_beat > 0:
            return []

        beat = int((tick // self._pulses_per_beat) % self._denominator)

        return self._symbol_decoder(self._pattern[beat])


class DrumSource(NoteSource):
    def __init__(self, note_number: int, denominator: int, pattern: str, velocity: int):
        self._pulses_per_beat = Clock.PPQN * 4 / denominator
        self._pattern = pattern
        self._denominator = denominator
        self._note_number = note_number
        self._velocity = velocity

    def get_notes(self, tick):
        if tick % self._pulses_per_beat > 0:
            return []

        beat = int((tick // self._pulses_per_beat) % self._denominator)

        result = []

        if self._pattern[beat] =='x':
            result.append(Note(note=self._note_number, velocity=self._velocity, tick_off=int(tick + self._pulses_per_beat)))
        
        return result


class NoteDespatcher(ClockWatcher, MessageSource):
    def __init__(self, clock: Clock, source: NoteSource, port):
        super().__init__()

        self._note_source = source
        self._notes_off = SortedList(key=lambda n: n.tick_off)
        self.port = port

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
