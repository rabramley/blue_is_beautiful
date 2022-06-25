from rich import traceback
from rich.align import Align
from textual.app import App
from textual.widget import Widget
from textual.widgets import ScrollView
from midi import Midi
import logging
import yaml

from midi.connectors import PortManager
from midi.project import Project

traceback.install()

with open('config.yaml') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

with open('project.yaml') as f:
    project = yaml.load(f, Loader=yaml.FullLoader)

logging.basicConfig(level=logging.WARN)


class Display(Widget):
    def on_mount(self):
        self.position_description = ''

    def render(self):
        return Align.center(self.position_description, vertical="middle")


class BlueApp(App):
    async def on_load(self, event):
        await self.bind("q", "quit")
        await self.bind("s", "toggle")
        self.port_manager = PortManager(config)
        self.midi = Midi(self.port_manager)
        self.project = Project(project, self.port_manager, self.midi)

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
        self.project._clock.toggle()

    async def tick(self):
        self._display.position_description = self.project.position_description()
        self._display.refresh()

    
BlueApp.run()
