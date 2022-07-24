from rich import traceback
import logging
import yaml

from midi.connectors import Midi, PortManager
from midi.project import Project

traceback.install()

with open('config.yaml') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

with open('project.yaml') as f:
    project = yaml.load(f, Loader=yaml.FullLoader)

logging.basicConfig(level=logging.WARN)


port_manager = PortManager(config)
midi = Midi(port_manager)
project = Project(project, port_manager, midi)

midi.start()
project._clock.start()

input("Press Enter to continue...")

project._clock.stop()
project._clock.join()
midi.stop()
midi.join()
