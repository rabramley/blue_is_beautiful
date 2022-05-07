from __future__ import annotations
import logging
import threading
import time
import queue
import mido
from mido import Message
from mido.ports import BasePort
from multiprocessing import Queue
from contextlib import contextmanager


class MidiConnector():
    def __init__(self, in_port_name: str, in_channel: int, out_port_name: str, out_channel: int):
        self.in_port_name = in_port_name
        self.in_channel = in_channel
        self.out_port_name = out_port_name
        self.out_channel = out_channel
    
    def set_midi_queue(self, midi_queue: Midi):
        self._midi_queue = midi_queue

    def send_message(self, message: Message):
        new_message = message.copy(channel=self.out_channel)
        logging.info(f'MidiConnector:send_message: sending message {new_message}')

        self._midi_queue.queue_message(self.out_port_name, new_message)

class MidiPort():
    def __init__(self, port: BasePort):
        self.port = port
        self.channels = []

        for i in range(16):
            self.channels.append([])
        
        port.callback = self.on_port_callback

    def register_connection(self, channel: int, connector: MidiConnector):
        self.channels[channel].append(connector)

    def on_port_callback(self, message: Message):
        logging.info(f'MidiPort:on_port_callback: received message: {message}')
        if hasattr(message, 'channel'): # Not all messages have channels
            for c in self.channels[message.channel]:
                c.send_message(message)


class MidiPortManager():
    def __init__(self):
        self.in_ports = {}
        self.out_ports = {}

    def get_in_port(self, port_name: str):
        if port_name in self.in_ports:
            return self.in_ports[port_name]
        
        for pn in mido.get_input_names():
            if pn.startswith(port_name):
                self.in_ports[port_name] = MidiPort(mido.open_input(pn))
                return self.in_ports[port_name]
        else:
            raise ValueError(f'Input MIDI port {port_name} not found')

    def get_out_port(self, port_name: str):
        if port_name in self.out_ports:
            return self.out_ports[port_name]
        
        for pn in mido.get_output_names():
            if pn.startswith(port_name):
                self.out_ports[port_name] = MidiPort(mido.open_output(pn))
                return self.out_ports[port_name]
        else:
            raise ValueError(f'Output MIDI port {port_name} not found')


class Midi(threading.Thread):
    def __init__(self):
        super().__init__()
        self._wallclock = time.time()
        self.queue = Queue()
        self._done = False
        self._port_manager = MidiPortManager()

    def register_connector(self, connector: MidiConnector):
        in_port = self._port_manager.get_in_port(connector.in_port_name)
        in_port.register_connection(connector.in_channel, connector)
        out_port = self._port_manager.get_out_port(connector.out_port_name)
        out_port.register_connection(connector.out_channel, connector)

        connector.set_midi_queue(self)

    def queue_message(self, port_name: str, message: Message):
        logging.info(f'Midi:queue_message: Queuing message {message} roport {port_name}')
        self.queue.put((message, port_name))

    def run(self):
        logging.info('Midi:run: Running')
        i = 0

        while not self._done:
            logging.info(f'Midi:run: looping')
            try:
                message, port_name = self.queue.get(timeout=1)
                logging.info(f'Midi:run: sending message {message} to port {port_name}')
                port = self._port_manager.get_out_port(port_name)
                port.port.send(message)
            except queue.Empty:
                logging.info(f'Midi:run: Empty')
                pass

    def stop(self):
        self._done = True


@contextmanager
def midi() -> Midi:
    result = Midi()

    try:
        logging.info('MIDI opening')

        result.start()

        yield result

    finally:
        logging.info('MIDI closing')

        result.stop()
        result.join()

        # del midiin
        # del midiout
