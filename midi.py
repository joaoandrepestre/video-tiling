from typing import Callable
from enum import Enum
from rtmidi import NoDevicesError, InvalidPortError, SystemError
from rtmidi.midiutil import open_midiinput
from rtmidi.midiconstants import NOTE_ON, NOTE_OFF, CONTROL_CHANGE
from config import MIDI_PORT_CONFIG, get_config
from threading import Thread
from time import sleep


class MidiMessageType(Enum):
    NOTE_ON = NOTE_ON
    NOTE_OFF = NOTE_OFF
    CONTROL_CHANGE = CONTROL_CHANGE


class Midi:

    # midi
    __midiin = None

    # threading
    __running: bool = False
    __connection_thread: Thread | None = None

    # callbacks
    __callbacks: dict[MidiMessageType,
                      set[Callable[[int, int], None]]] = dict()

    def __init__(self):
        self.__running = True
        self.__connection_thread = Thread(
            group=None, target=self.__try_connect_device)
        self.__connection_thread.start()

    def subscribe(self, type: MidiMessageType, callback: Callable[[int, int], None]) -> None:
        callbacks = self.__callbacks.get(type, set())
        callbacks.add(callback)
        self.__callbacks[type] = callbacks

    def __callback(self, event: tuple[tuple[int, int, int], float], data: object = None) -> None:
        message, _ = event
        status, arg1, arg2 = message
        try:
            type = MidiMessageType(status)
            print(
                f'Midi event of type {type.name} was triggered with args: {(arg1, arg2)}')
            callbacks = self.__callbacks.get(type, [])
            for callback in callbacks:
                callback(arg1, arg2)
        except ValueError:
            print(
                f'Midi event of unknown type {status} was triggered with args: {(arg1, arg2)}')

    def is_device_connected(self) -> bool:
        return self.__midiin is not None

    def __try_connect_device(self) -> None:
        delay = 1
        previous_result = False
        while (self.__running):
            if (delay > 10.0):
                break
            portnum = get_config(MIDI_PORT_CONFIG)
            try:
                self.__midiin, _ = open_midiinput(portnum, interactive=False)
                self.__midiin.set_callback(self.__callback)
            except (NoDevicesError, InvalidPortError):
                self.__midiin = None
            except SystemError:
                pass
            if (self.is_device_connected() == previous_result):
                delay += 0.5
            else:
                delay = 1
            previous_result = self.is_device_connected()
            sleep(delay)

    def __wait_threads(self) -> None:
        if (self.__connection_thread.is_alive()):
            self.__connection_thread.join()

    def destroy(self):
        self.__running = False
        self.__wait_threads()
        if self.is_device_connected():
            self.__midiin.close_port()
        del self.__midiin
