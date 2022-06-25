from midi.clock import Clock
from midi.sequencing import SequencerTrack


class Project:
    def __init__(self, project_data, port_manager, midi):
        self._project_data = project_data
        self._port_manager = port_manager
        self._midi = midi
        self._connectors = []
        self._sequencers = []

        self._clock = Clock(bpm=project_data['bpm'])
        # self._midi.register_clock(self._clock)
        self._clock.attach_watcher(midi)

        self._register_connectors()
        self._register_sequencers()
    
    def _register_connectors(self):
        for c in self._project_data['connectors']:
            source = self._port_manager.get_in_channel(c['in_port_name'], c['in_channel'])
            if source:
                source.register_observer(self._port_manager.get_out_channel(c['out_port_name'], c['out_channel'], self._midi))
    
    def _register_sequencers(self):
        source = SequencerTrack(self._clock, 30, 100, 2)
        source.register_observer(self._port_manager.get_out_channel('Cycles', 1, self._midi))
        self._sequencers.append(source)

        source = SequencerTrack(self._clock, 30, 100, 4)
        source.register_observer(self._port_manager.get_out_channel('Cycles', 0, self._midi))
        self._sequencers.append(source)

        source = SequencerTrack(self._clock, 30, 100, 8)
        source.register_observer(self._port_manager.get_out_channel('Cycles', 2, self._midi))
        self._sequencers.append(source)

    def position_description(self):
        return f'{self._clock._tick} {self._clock._running} {self._clock._interval / 1_000_000}'
