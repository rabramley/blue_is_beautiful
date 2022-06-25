from __future__ import annotations
import logging
from contextlib import contextmanager
from midi.connectors import Midi, PortManager


@contextmanager
def midi(port_manager: PortManager) -> Midi:
    result = Midi(port_manager)

    try:
        logging.info('MIDI opening')

        result.start()

        yield result

    finally:
        logging.info('MIDI closing')

        result.stop()
        result.join()

        # del midiin
        # del midiout
