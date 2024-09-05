from __future__ import annotations
from dataclasses import dataclass
from itertools import chain
from mido import Message
from midi.clock import Clock, ClockWatcher
from midi.connections import MessageSource
from sortedcontainers import SortedList
from midi.connectors import PortManager
from midi.scales import Scale
from copy import deepcopy
from typing import Self
from midi.connectors import PortManager


class Instrument:
    def __init__(self, config: dict, port_manager: PortManager):
        super().__init__()

        self.name = config['name']
        self.pattern_type = config['pattern_type']
        self.port = port_manager.get_out_channel(config['port'], config['channel'])
        self.default_symbol_mapper = SymbolMapper(config.get('defaults', {}).get('symbols', []))

        self.timbres = {
            c['name']: Timbre(c, self.default_symbol_mapper)
            for c in config.get('timbres', [])
        }


class SymbolMapping:
    def __init__(self, config: list, df_note=None, df_velocity=None) -> None:
        self.symbol = config['symbol']
        self.velocity = config.get('velocity', df_velocity)
        self.note = config.get('note', df_note)

    def apply_defaults(self, defaults: Self):
        self.velocity = self.velocity or defaults.velocity
        self.note = self.note or defaults.note

    def apply_default_values(self, df_note: int, df_velocity: int):
        self.velocity = self.velocity or df_velocity
        self.note = self.note or df_note


class SymbolMapper:
    def __init__(self, config: list, df_note=None, df_velocity=None) -> None:
        self.df_note = df_note
        self.df_velocity = df_velocity
        self.map: dict = {
            s.symbol: s
            for s in [
                SymbolMapping(c, df_note, df_velocity) for c in config
            ]
        }

    def apply_defaults(self, defaults: Self):
        for k, v in defaults.map.items():
            if k not in self.map:
                m: SymbolMapping = deepcopy(v)
                m.apply_default_values(
                    self.df_note,
                    self.df_velocity,
                )
                self.map[k] = m
            else:
                self.map[k].apply_defaults(v)


class Timbre:
    def __init__(self, config: dict, df_symbol_mapper: SymbolMapper) -> None:
        self.name: str = config['name']
        self.symbol_mapper: SymbolMapper = SymbolMapper(
            config=config.get('symbols', []),
            df_note=config.get('note', None),
            df_velocity=config.get('velocity', None),
        )
        self.symbol_mapper.apply_defaults(df_symbol_mapper)


class Part:
    def __init__(self, config: dict, instruments: dict[Instrument]) -> None:
        self.instrument_name: str = config.get('instrument', None)
        self.instrument: Instrument = instruments.get(self.instrument_name, None)
        self.timing: Timing = Timing(config)

        self.symbol_mapper = SymbolMapper(
            config=config.get('symbols', []),
            df_note=config.get('note', None),
            df_velocity=config.get('velocity', None),
        )

        self.symbol_mapper.apply_defaults(self.instrument.default_symbol_mapper)

        self.patterns = []

        for timbre_name, pattern in config.get('patterns', {}).items():
            timbre_mapper: Timbre = self.instrument.timbres[timbre_name]
            self.patterns.append(SymbolPattern(
                pattern=pattern,
                symbol_mapper=timbre_mapper.symbol_mapper,
                timing=self.timing,
            ))


class SymbolPattern:
    def __init__(self, pattern: str, symbol_mapper: SymbolMapper, timing: Timing) -> None:
        self.timing = timing
        self.pattern = pattern.split()
        self.symbol_mapper = symbol_mapper

    def get_notes(self, tick) -> list[Note]:
        result: list[Note] = []

        beat = self.timing.get_beat(tick)

        if beat:
            i: int = int(beat % len(self.pattern))
            symbol = self.pattern[i]
            m: SymbolMapper = self.symbol_mapper.map[symbol]

            if m.velocity:
                result.append(Note(
                    note=m.note,
                    velocity=m.velocity,
                    tick_off=self.timing.get_next_tick_for_length(tick, 1),
                ))
        
        return result


class Timing:
    def __init__(self, config: dict) -> None:
        self.denominator = config.get('denominator', None)

    def set_ppqn(self, ppqn):
        self.ticks_per_beat = ppqn * 4 / self.denominator
        
    def get_beat(self, tick: int):
        if tick % self.ticks_per_beat > 0:
            return None
        
        return tick // self.ticks_per_beat
    
    def get_next_tick_for_length(self, tick: int, beat_length: int) -> int:
        return tick + (self.ticks_per_beat * beat_length)

        
class PatternPlayer(ClockWatcher, MessageSource):
    def __init__(self, clock: Clock, pattern: SymbolPattern) -> None:
        super().__init__()
        
        self.clock: Clock = clock
        self.pattern: SymbolPattern = pattern
        self._notes_off = SortedList(key=lambda n: n.tick_off)

        self.pattern.timing.set_ppqn(clock.PPQN)
        clock.attach_watcher(self)

    def tick(self, tick):
        split_point = self._notes_off.bisect_right(Note(note=0, velocity=0, tick_off=tick))

        for o in (self._notes_off.pop(index=0) for _ in range(split_point)):
            self.send_message(Message('note_off', channel=0, note=o.note, velocity=o.velocity, time=0))

        for n in self.pattern.get_notes(tick):
            self.send_message(Message('note_on', channel=0, note=n.note, velocity=n.velocity, time=0))
            self._notes_off.add(n)

    def restart(self):
        pass


def get_part_patterns(config: list, instruments: dict[Instrument], clock: Clock):
    result = []

    for c in config:
        part = Part(c, instruments)

        for p in part.patterns:
            pp = PatternPlayer(
                clock=clock,
                pattern=p,
            )
            pp.register_observer(part.instrument.port)
            result.append(pp)

    return result


@dataclass
class Note():
    note: int
    velocity: int
    tick_off: int
