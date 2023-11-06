from midi.connectors import PortManager


class Instrument:
    def __init__(self, config: dict, port_manager: PortManager):
        super().__init__()

        self.name = config['name']
        self.note_map = {
            nm['symbol']: nm['note']
            for nm in config.get('note_map', [])
        }
        self._port = port_manager.get_out_channel(config['port'], config['channel'])
