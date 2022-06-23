from rich import traceback
from rich.align import Align
from textual.app import App
from textual.widget import Widget
from textual.widgets import ScrollView
from midi import Clock, Midi, MidiConnector, PortManager, SequencerTrack
from textual.reactive import Reactive
import logging
import yaml

traceback.install()

with open('config.yaml') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

logging.basicConfig(level=logging.WARN)

class Display(Widget):
    def on_mount(self):
        self.interval = ''
        self.next = ''
        self.tick = ''

    def render(self):
        return Align.center(f'{self.interval}: {self.next}  {self.tick}', vertical="middle")


class BlueApp(App):
    async def on_load(self, event):
        await self.bind("q", "quit")
        await self.bind("s", "toggle")
        self.port_manager = PortManager(config)
        self.midi = Midi(self.port_manager)

        for c in config['connectors']:
            m = MidiConnector(
                midi_queue = self.midi,
                in_channel = self.port_manager.get_in_channel(c['in_port_name'], c['in_channel']),
                out_channel = self.port_manager.get_out_channel(c['out_port_name'], c['out_channel']),
            )

        self.clock = Clock(bpm=config['bpm'])
        self.midi.register_clock(self.clock)

        MidiConnector(
            midi_queue = self.midi,
            in_channel = SequencerTrack(self.clock, 30, 100, 2),
            out_channel = self.port_manager.get_out_channel('Cycles', 1),
        )
        MidiConnector(
            midi_queue = self.midi,
            in_channel = SequencerTrack(self.clock, 30, 100, 4),
            out_channel = self.port_manager.get_out_channel('Cycles', 0),
        )
        MidiConnector(
            midi_queue = self.midi,
            in_channel = SequencerTrack(self.clock, 30, 100, 8),
            out_channel = self.port_manager.get_out_channel('Cycles', 2),
        )

        self.midi.start()

    async def on_mount(self):
        self._display = Display()
        self._log_view = ScrollView()
        await self.view.dock(self._log_view, edge="left", size=48, name="sidebar")
        await self.view.dock(self._display, edge="top")
        self.set_interval(1, self.tick)
    
    async def shutdown(self):
        await super().shutdown()

        self.midi.stop()
        self.midi.join()

    async def action_toggle(self):
        self.clock.toggle()

    async def tick(self):
        self._display.interval = self.clock._interval
        self._display.next = self.clock._next
        self._display.tick = self.clock._tick
        self._display.refresh()

    
BlueApp.run()
