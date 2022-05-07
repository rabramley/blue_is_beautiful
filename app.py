import time
from midi import midi, MidiConnector
import logging
import yaml


with open('config.yaml') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

logging.basicConfig(level=logging.INFO)

with midi() as midi:
    for c in config['connectors']:
        midi.register_connector(MidiConnector(**c))

    while True:
        time.sleep(1)
