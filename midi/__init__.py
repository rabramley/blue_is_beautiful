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
    def __init__(
        self,
        midi_queue: Midi,
        in_channel: InChannel,
        out_channel: OutChannel,
    ):
        self._midi_queue = midi_queue
        self.in_channel = in_channel
        self.out_channel = out_channel

        if in_channel and out_channel:
            in_channel.register_observer(self)
    
    def send_message(self, message: Message):
        new_message = message.copy(channel=self.out_channel.channel)
        logging.info(f'MidiConnector:send_message: sending message {new_message}')

        self._midi_queue.queue_message(self.out_channel.port_name, new_message)


class InChannel():
    def __init__(self):
        self._observers = []

    def register_observer(self, connector: MidiConnector):
        self._observers.append(connector)

    def send_message(self, message: Message):
        for c in self._observers:
            c.send_message(message)


class OutChannel():
    def __init__(self, port_name: str, channel: int):
        self.port_name = port_name
        self.channel = channel


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

    def get_out_channel(self, port_name: str, channel: int):
        if port_name in self.out_ports:
            return OutChannel(port_name, channel)

class ClockWatcher():
    def tick(self, tick):
        pass


class SequencerTrack(ClockWatcher, InChannel):
    def __init__(self, clock: Clock, note: int, velocity: int, denominator: int):
        super().__init__()

        self._note = note
        self._velocity = velocity
        self._connectors = []
        self._pulses_per_beat = Clock.PPQN * 4 / denominator

        clock.attach_watcher(self)

    def tick(self, tick):
        if tick % self._pulses_per_beat == 0:
            self.beat()
    
    def beat(self):
        self.send_message(Message('note_on', channel=0, note=self._note, velocity=self._velocity, time=0))


class PortClock(ClockWatcher):
    def __init__(self, midi_queue: Midi, port_manager: PortManager, port_name: str):
        self._midi_queue = midi_queue
        self._port_manager = port_manager
        self._port_name = port_name

    def tick(self, tick):
        self._midi_queue.queue_message(self._port_name, Message('clock'))


class Clock():
    NANO_SECONDS_PER_MINUTE = 60_000_000_000
    PPQN = 24

    def __init__(self, bpm: int):
        self._interval = int(Clock.NANO_SECONDS_PER_MINUTE / bpm / Clock.PPQN)
        self._tick = 0
        self._running = False
        self._watchers = []
        self._next = 0
    
    def attach_watcher(self, watcher: ClockWatcher):
        self._watchers.append(watcher)

    def start(self):
        self._tick = 0
        self._next = time.monotonic_ns() + self._interval
        self._running = True

    def stop(self):
        self._tick = 0
        self._running = False

    def toggle(self):
        if self._running:
            self.stop()
        else:
            self.start()

    def tick(self):
        if not self._running:
            return

        if self._next < time.monotonic_ns():
            self._tick += 1
            self._next += self._interval

            for w in self._watchers:
                logging.info(f'MidiConnector:send_message: sending tick')
                w.tick(self._tick)


class Midi(threading.Thread):
    def __init__(self, port_manager: PortManager):
        super().__init__()
        self._wallclock = time.time()
        self.queue = Queue()
        self._done = False
        self._port_manager = port_manager
        self._clocks = []

    def register_clock(self, clock: Clock):
        self._clocks.append(clock)

    def queue_message(self, port_name: str, message: Message):
        logging.info(f'Midi:queue_message: Queuing message {message} to port {port_name}')
        self.queue.put((message, port_name))

    def run(self):
        logging.info('Midi:run: Running')
        
        while not self._done:
            logging.info(f'Midi:run: looping')

            for c in self._clocks:
                c.tick()

            try:
                message, port_name = self.queue.get(timeout=0.01)
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
