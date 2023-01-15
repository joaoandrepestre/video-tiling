from typing import Callable
import rtmidi
from rtmidi.midiutil import open_midiinput
from rtmidi.midiconstants import NOTE_ON, CONTROL_CHANGE
from config import MIDI_CONFIG, MIDI_PORT_CONFIG, get_config
from threading import Thread


class Midi:
    def __init__(self):
        self.midiin = None
        self.running: bool = False
        self.read_thread: Thread = Thread(
            group=None, target=self.read_from_queue)
        self.try_connect_device()
        self.note_callbacks: list[Callable] = []
        self.knob_callbacks: list[Callable] = []

    def register_note_callback(self, callback: Callable):
        self.note_callbacks.append(callback)

    def trigger_note_callbacks(self, note: int, velocity: int):
        for callback in self.note_callbacks:
            callback(note, velocity)

    def register_knob_callback(self, callback: Callable):
        self.knob_callbacks.append(callback)

    def trigger_knob_callbacks(self, knob: int, value: int):
        for callback in self.knob_callbacks:
            callback(knob, value)

    def is_device_connected(self) -> bool:
        return self.midiin is not None

    def try_connect_device(self) -> bool:
        portnum = get_config(MIDI_PORT_CONFIG)
        try:
            self.midiin, _ = open_midiinput(portnum, interactive=False)
        except (rtmidi.NoDevicesError, rtmidi.InvalidPortError):
            self.midiin = None
        except rtmidi.SystemError:
            pass
        connected = self.is_device_connected()
        if connected:
            self.running = True
            self.read_thread.start()
        return connected

    def read_from_queue(self):
        while (self.running):
            self.get_midi_note()

    def get_midi_note(self) -> str:
        if self.midiin is None:
            return None
        msg = self.midiin.get_message()
        if msg is None:
            return None
        [status, note, velocity] = msg[0]
        if status != NOTE_ON or velocity == 0:
            return None
        self.trigger_note_callbacks(note, velocity)
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
        self.running = False
        self.read_thread.join()
        if self.midiin is not None:
            self.midiin.close_port()
        del self.midiin
