from rich import traceback
from rich.align import Align
from textual.app import App
from textual.widget import Widget
from midi import Clock, Midi, MidiConnector, PortManager
import logging
import yaml

traceback.install()

with open('config.yaml') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

logging.basicConfig(level=logging.WARN)
# logging.basicConfig(level=logging.INFO)

class Display(Widget):
    def on_mount(self):
        self.interval = ''
        self.next = ''
        self.beat = ''

    def render(self):
        return Align.center(f'{self.interval}: {self.next}  {self.beat}', vertical="middle")


class BlueApp(App):
    async def on_load(self, event):
        await self.bind("q", "quit")
        self.port_manager = PortManager(config)
        self.midi = Midi(self.port_manager)

        for c in config['connectors']:
            self.midi.register_connector(MidiConnector(**c))

        self.clock = Clock(bpm=config['bpm'])
        self.midi.register_clock(self.clock)

        self.midi.start()

    async def on_mount(self):
        self._display = Display()
        await self.view.dock(self._display)
        self.set_interval(1, self.tick)
    
    async def shutdown(self):
        await super().shutdown()

        self.midi.stop()
        self.midi.join()

    async def tick(self):
        self._display.interval = self.clock.interval
        self._display.next = self.clock.next
        self._display.beat = self.clock.beat
        self._display.refresh()

    
BlueApp.run()
