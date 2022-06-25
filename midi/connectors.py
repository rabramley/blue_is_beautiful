from __future__ import annotations
import mido
from mido import Message 
from mido.ports import BasePort
import logging
from midi.connections import MessageDestination, MessageSource
from midi.sequencing import Clock
import logging
import threading
import queue
from mido import Message
from multiprocessing import Queue
from midi.sequencing import Clock


class PortManager():
    def __init__(self, config):
        self.in_ports = {}
        self.out_ports = {}

        for p in config['ports']:
            in_port = self._find_in_port(p['port_name'])

            if in_port:
                self.in_ports[p['name']] = InPort(in_port, p['name'])
            else:
                logging.warn(f"PortManager():__init__ {p['port_name']} in port not found.  Ignoring.")

            out_port = self._find_out_port(p['port_name'])

            if out_port:
                self.out_ports[p['name']] = OutPort(out_port, p['name'])
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

    def get_in_channel(self, port_name: str, channel: int):
        if port_name in self.in_ports:
            return self.in_ports[port_name].channels[channel]

    def get_out_channel(self, port_name: str, channel: int, midi_queue: Midi):
        if port_name in self.out_ports:
            return OutChannel(port_name, channel, midi_queue)


class Midi(threading.Thread):
    def __init__(self, port_manager: PortManager):
        super().__init__()
        self.queue = Queue()
        self._done = False
        self._port_manager = port_manager
        self._clocks = []

    def register_clock(self, clock: Clock):
        self._clocks.append(clock)

    def queue_message(self, port_name: str, message: Message):
        self.queue.put((message, port_name))

    def run(self):
        while not self._done:
            for c in self._clocks:
                c.tick()

            try:
                message, port_name = self.queue.get(timeout=0.01)
                port = self._port_manager.out_ports[port_name]
                port.port.send(message)
            except queue.Empty:
                pass

    def stop(self):
        self._done = True


class InChannel(MessageSource):
    pass


class OutChannel(MessageDestination):
    def __init__(self, port_name: str, channel: int, midi_queue: Midi):
        self.port_name = port_name
        self.channel = channel
        self._midi_queue = midi_queue

    def receive_message(self, message: Message):
        new_message = message.copy(channel=self.channel)
        self._midi_queue.queue_message(self.port_name, new_message)


class InPort():
    def __init__(self, port: BasePort, name: str):
        self.port = port
        self.name = name
        self.channels = []

        for i in range(16):
            self.channels.append(InChannel())
        
        port.callback = self.on_port_callback

    def on_port_callback(self, message: Message):
        if hasattr(message, 'channel'): # Not all messages have channels
            self.channels[message.channel].send_message(message)


class OutPort():
    def __init__(self, port: BasePort, name: str):
        self.port = port
        self.name = name
