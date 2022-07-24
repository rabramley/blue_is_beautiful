import logging
from midi.clock import Clock
from midi.sequencing import MidiClockSender, SequencerTrack


class Project:
    def __init__(self, project_data, port_manager, midi):
        self._project_data = project_data
        self._port_manager = port_manager
        self._midi = midi
        self._connectors = []
        self._sequencers = []

        self._clock = Clock(bpm=project_data['bpm'])

        self._register_connectors()
        self._register_sequencers()
        self._register_clocks()
    
    def _register_connectors(self):
        for c in self._project_data['connectors']:
            source = self._port_manager.get_in_channel(c['in_port_name'], c['in_channel'])
            if source:
                logging.info(f"Registering connection: {c['in_port_name']}:{c['in_channel']}  -> {c['out_port_name']}:{c['out_channel']}")
                source.register_observer(self._port_manager.get_out_channel(c['out_port_name'], c['out_channel'], self._midi))
    
    def _register_sequencers(self):
        for s in self._project_data['sequence_tracks']:
            source = SequencerTrack(self._clock, s['note'], s['velocity'], s['denominator'], s['pattern'])
            source.register_observer(self._port_manager.get_out_channel(s['port'], s['channel'], self._midi))
            self._sequencers.append(source)

    def _register_clocks(self):
        for c in self._project_data['clock']:
            MidiClockSender(c['out_port_name'].lower(), self._midi, self._clock)

    def position_description(self):
        return f'{self._clock._tick} {self._clock._running} {self._clock._interval / 1_000_000}'
