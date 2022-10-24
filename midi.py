import rtmidi
from rtmidi.midiutil import open_midiinput
from rtmidi.midiconstants import NOTE_OFF
from config import MIDI_CONFIG, MIDI_PORT_CONFIG, get_config


class Midi:
    def __init__(self):
        self.midiin = None
        self.try_connect_device()

    def is_device_connected(self) -> bool:
        return self.midiin is not None

    def try_connect_device(self) -> bool:
        if self.is_device_connected():
            return True
        portnum = get_config(MIDI_PORT_CONFIG)
        try:
            self.midiin, _ = open_midiinput(portnum)
        except rtmidi.NoDevicesError:
            self.midiin = None
        return self.is_device_connected()

    def get_midi_note(self) -> str:
        if self.midiin is None:
            return None
        msg = self.midiin.get_message()
        if msg is None:
            return None
        [status, note, velocity] = msg[0]
        if status == NOTE_OFF:
            return None
        return f'{note}'

    def get_midi_input(self) -> int:
        if self.midiin is None:
            return None

        note = self.get_midi_note()
        midi_map: list = get_config(MIDI_CONFIG)
        try:
            return midi_map.index(f'{note}')
        except ValueError:
            return None

    def destroy(self):
        if self.midiin is not None:
            self.midiin.close_port()
        del self.midiin
