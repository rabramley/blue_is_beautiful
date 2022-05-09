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
        self._active = False
    
    def attach_to_midi(self, midi_queue: Midi, port_manager: PortManager):
        if not self.in_port_name in port_manager.in_ports:
            logging.warn(f"MidiConnector():attach_to_midi in port {self.in_port_name} not found.  Ignoring.")
            return
        if not self.out_port_name in port_manager.out_ports:
            logging.warn(f"MidiConnector():attach_to_midi out port {self.out_port_name} not found.  Ignoring.")
            return

        in_port = port_manager.in_ports[self.in_port_name]
        in_port.register_connection(self.in_channel, self)
        out_port = port_manager.out_ports[self.out_port_name]
        out_port.register_connection(self.out_channel, self)

        self._midi_queue = midi_queue
        self.out_port_name_actual = out_port.name

        self._active = True

    def send_message(self, message: Message):
        if not self._active:
            return

        new_message = message.copy(channel=self.out_channel)
        logging.info(f'MidiConnector:send_message: sending message {new_message}')

        self._midi_queue.queue_message(self.out_port_name_actual, new_message)


class Port():
    def __init__(self, port: BasePort, name: str):
        self.port = port
        self.name = name
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


class PortManager():
    def __init__(self, config):
        self.in_ports = {}
        self.out_ports = {}

        for p in config['ports']:
            in_port = self._find_in_port(p['port_name'])

            if in_port:
                self.in_ports[p['name']] = Port(in_port, p['name'])
            else:
                logging.warn(f"PortManager():__init__ {p['port_name']} in port not found.  Ignoring.")

            out_port = self._find_out_port(p['port_name'])

            if out_port:
                self.out_ports[p['name']] = Port(out_port, p['name'])
            else:
                logging.warn(f"PortManager():__init__ {p['port_name']} out port not found.  Ignoring.")

    def _find_in_port(self, port_name: str):
        for port_name_actual in mido.get_input_names():
            if port_name_actual.startswith(port_name):
                return mido.open_input(port_name_actual)

    def _find_out_port(self, port_name: str):
        for port_name_actual in mido.get_output_names():
            if port_name_actual.startswith(port_name):
                return mido.open_output(port_name_actual)


class Midi(threading.Thread):
    def __init__(self, port_manager: PortManager):
        super().__init__()
        self._wallclock = time.time()
        self.queue = Queue()
        self._done = False
        self._port_manager = port_manager

    def register_connector(self, connector: MidiConnector):
        connector.attach_to_midi(self, self._port_manager)

    def queue_message(self, port_name: str, message: Message):
        logging.info(f'Midi:queue_message: Queuing message {message} roport {port_name}')
        self.queue.put((message, port_name))

    def run(self):
        logging.info('Midi:run: Running')

        while not self._done:
            logging.info(f'Midi:run: looping')
            try:
                message, port_name = self.queue.get(timeout=1)
                logging.info(f'Midi:run: sending message {message} to port {port_name}')
                port = self._port_manager.out_ports[port_name]
                port.port.send(message)
            except queue.Empty:
                logging.info(f'Midi:run: Empty')

    def stop(self):
        self._done = True


@contextmanager
def midi(port_manager: PortManager) -> Midi:
    result = Midi(port_manager)

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
