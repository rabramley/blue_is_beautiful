from datetime import datetime
from rich.align import Align
from textual.app import App
from textual.widget import Widget
from midi import Midi, midi, MidiConnector, PortManager
import logging
import yaml


with open('config.yaml') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

logging.basicConfig(level=logging.WARN)
# logging.basicConfig(level=logging.INFO)


class Clock(Widget):
    def on_mount(self):
        self._value = ''

    def render(self):
        return Align.center(self._value, vertical="middle")

    def v(self, value):
        self._value = value
        self.refresh()


class BlueApp(App):
    async def on_load(self, event):
        await self.bind("q", "quit")
        self.port_manager = PortManager(config)
        self.midi = Midi(self.port_manager)
        self.midi.start()

        for c in config['connectors']:
            self.midi.register_connector(MidiConnector(**c))

    async def on_mount(self):
        self._clock = Clock()
        await self.view.dock(self._clock)
        self.set_interval(1, self.tick)
    
    async def shutdown(self):
        await super().shutdown()

        self.midi.stop()
        self.midi.join()

    async def tick(self):
        time = datetime.now().strftime("%c")
        self._clock.v(f'iuhweh {time}')

    
BlueApp.run()
