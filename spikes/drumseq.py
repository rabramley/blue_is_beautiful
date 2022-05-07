#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# drumseq.py
#
# MIDI Drum sequencer prototype, by Michiel Overtoom, motoom@xs4all.nl
#
"""Play drum pattern from file to MIDI out."""

from __future__ import print_function

import argparse
import sys
import threading

from random import gauss
from time import sleep, time as timenow

import rtmidi
from rtmidi.midiutil import open_midioutput
from rtmidi.midiconstants import (
    ALL_SOUND_OFF,
    NOTE_ON,
    NOTE_OFF,
)


FUNKYDRUMMER = """
    #    1...|...|...|...
    60 0 x.x.......x..x.. Bassdrum
    60 1 ....x..m.m.mx..m Snare
    60 2 xxxxx.x.xxxxx.xx Closed Hi-hat
    60 3 .....x.x.....x.. Open Hi-hat
"""


UNFUNKYDRUMMER = """
    #    1...|...|...|...
    60 0 x.......x....... Bassdrum
    60 1 ....x..s.m.sx..+ Snare
    60 2 xxxxxxx.xxxxxxxx Closed Hi-hat
    60 3 .......x........ Open Hi-hat
"""


class Sequencer(threading.Thread):
    """MIDI output and scheduling thread."""

    def __init__(self, midiout, pattern, bpm=100, volume=127):
        super(Sequencer, self).__init__()
        self.midiout = midiout
        self.bpm = max(20, min(bpm, 400))
        self.interval = 15. / self.bpm
        self.pattern = pattern
        self.volume = volume
        self.start()

    def run(self):
        self.done = False
        self.callcount = 0

        # give MIDI instrument some time to activate drumkit
        sleep(0.3)
        self.started = timenow()

        while not self.done:
            self.worker()
            self.callcount += 1
            # Compensate for drift:
            # calculate the time when the worker should be called again.
            nexttime = self.started + self.callcount * self.interval
            timetowait = max(0, nexttime - timenow())
            if timetowait:
                sleep(timetowait)
            else:
                print("Oops!")

    def worker(self):
        self.pattern.playstep(self.midiout)


class Drumpattern(object):
    """Container and iterator for a multi-track step sequence."""

    velocities = {
        "-": None,  # continue note
        ".": 0,     # off
        "+": 10,    # ghost
        "s": 60,    # soft
        "m": 100,   # medium
        "x": 120,   # hard
    }

    def __init__(self, pattern):
        self.instruments = []

        pattern = (line.strip() for line in pattern.splitlines())
        pattern = (line for line in pattern if line and line[0] != '#')

        for line in pattern:
            parts = line.split(" ", 3)
            print(parts)

            if len(parts) == 4:
                patch, channel, strokes, description = parts
                patch = int(patch)
                self.instruments.append((patch, channel, strokes))
                self.steps = len(strokes)

        self.step = 0
        self._notes = {}

    def reset(self):
        self.step = 0

    def playstep(self, midiout):
        for note, chan, strokes in self.instruments:
            char = strokes[self.step]
            velocity = self.velocities.get(char)

            if velocity is not None:
                if self._notes.get(note):
                    midiout.send_message([NOTE_OFF | int(chan), note, 0])
                    self._notes[note] = 0
                if velocity > 0:
                    midiout.send_message([NOTE_ON | int(chan), note, max(1, velocity)])
                    self._notes[note] = velocity

        self.step += 1

        if self.step >= self.steps:
            self.step = 0


def main(args=None):
    pattern = UNFUNKYDRUMMER
    port = 5
    channel = 0

    pattern = Drumpattern(pattern)

    try:
        midiout, port_name = open_midioutput(
            port,
            api=rtmidi.API_UNIX_JACK,
            client_name="drumseq",
            port_name="MIDI Out")
    except (EOFError, KeyboardInterrupt):
        return

    seq = Sequencer(midiout, pattern)

    print("Playing drum loop at %.1f BPM, press Control-C to quit." % seq.bpm)

    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        print('')
    finally:
        seq.done = True  # And kill it.
        seq.join()
        midiout.close_port()
        del midiout
        print("Done")


if __name__ == "__main__":
    sys.exit(main() or 0)