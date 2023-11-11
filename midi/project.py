import logging
from midi.clock import Clock
from midi.sequencing import Instrument, get_part_patterns
from midi.clock import MidiClockSender
from midi.connectors import PortManager, Midi


class Project:
    def __init__(self, project_data: dict, port_manager: PortManager, midi: Midi):
        self._project_data = project_data
        self._port_manager = port_manager
        self._midi = midi
        self._connectors = []
        self._sequencers = []
        self._instruments = {}

        self._clock = Clock(bpm=project_data['bpm'])

        self._register_connectors()
        self._register_instruments()
        self._register_sequencers()
        self._register_clocks()
    
    def _register_connectors(self):
        if 'connectors' not in self._project_data:
            return

        for c in self._project_data['connectors']:
            source = self._port_manager.get_in_channel(c['in_port_name'], c['in_channel'])
            if source:
                logging.info(f"Registering connection: {c['in_port_name']}:{c['in_channel']}  -> {c['out_port_name']}:{c['out_channel']}")
                source.register_observer(self._port_manager.get_out_channel(c['out_port_name'], c['out_channel']))
    
    def _register_instruments(self):
        for i in self._project_data.get('instruments', []):
            source = Instrument(i, self._port_manager)
            self._instruments[source.name] = source
    
    def _register_sequencers(self):
        self._sequencers = get_part_patterns(
            config=self._project_data.get('parts', []),
            instruments=self._instruments,
            clock=self._clock,
        )

    def _register_clocks(self):
        for c in self._project_data['clock']:
            MidiClockSender(c['out_port_name'].lower(), self._midi, self._clock)

    def position_description(self):
        return f'{self._clock._tick} {self._clock._running} {self._clock._interval / 1_000_000}'
