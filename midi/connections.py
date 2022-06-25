from mido import Message

class MessageDestination():
    def receive_message(self, message: Message):
        pass


class MessageSource():
    def __init__(self):
        self._observers = []

    def register_observer(self, destination: MessageDestination):
        if destination:
            self._observers.append(destination)

    def send_message(self, message: Message):
        for o in self._observers:
            o.receive_message(message)
