from rich import traceback
import logging
import yaml

from midi.connectors import Midi, PortManager
from midi.project import Project
from time import sleep

traceback.install()

with open('config.yaml') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

with open('song.yaml') as f:
    project = yaml.load(f, Loader=yaml.FullLoader)

logging.basicConfig(level=logging.WARN)

port_manager = PortManager(config)
port_manager.debug_ports()

midi = Midi(port_manager)
project = Project(project, port_manager, midi)

midi.start()
project._clock.start()
project._clock.toggle()

input("Press Enter to continue...")

project._clock.stop()
project._clock.join()

sleep(0.2)

midi.stop()
midi.join()
