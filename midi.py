from typing import Callable
from enum import Enum
from rtmidi import NoDevicesError, InvalidPortError, SystemError
from rtmidi.midiutil import open_midiinput
from rtmidi.midiconstants import NOTE_ON, NOTE_OFF, CONTROL_CHANGE
from config import MIDI_CONFIG, MIDI_PORT_CONFIG, get_config
from threading import Thread, Lock
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
    __lock: Lock = None
    __connection_thread: Thread | None = None

    # callbacks
    __callbacks: dict[MidiMessageType,
                      set[Callable[[int, int], None]]] = dict()

    def __init__(self):
        self.__running = True
        self.__lock = Lock()
        self.__connection_thread = Thread(
            group=None, target=self.__try_connect_device)
        self.__connection_thread.start()

    def subscribe(self, type: MidiMessageType, callback: Callable[[int, int], None]) -> None:
        callbacks = self.__callbacks.get(type, set())
        callbacks.add(callback)
        self.__callbacks[type] = callbacks
        self.__register_callbacks()

    def __register_callbacks(self) -> None:
        if (self.is_device_connected()):
            self.__midiin.set_callback(self.__callback_builder())

    def __callback_builder(self) -> Callable[[tuple[list, float], object], None]:
        def callback(event, data=None):
            message, _ = event
            status, arg1, arg2 = message
            try:
                received_type = MidiMessageType(status)
                print(
                    f'Midi event of type {received_type.name} was triggered with args: {(arg1, arg2)}')
                for (type, callbacks) in self.__callbacks.items():
                    if (received_type is not type):
                        continue
                    for callback in callbacks:
                        callback(arg1, arg2)
            except ValueError:
                print(
                    f'Midi event of unknown type {status} was triggered with args: {(arg1, arg2)}')
        return callback

    def __trigger_callbacks(self, status: int, arg1: int, arg2: int) -> None:
        try:
            type = MidiMessageType(status)
            print(
                f'Midi event of type {type.name} was triggered with args: {(arg1, arg2)}')
            callbacks = self.__callbacks.get(type)
            if (callbacks is None):
                return
            for callback in callbacks:
                callback(arg1, arg2)
        except ValueError:
            print(
                f'Midi event of unknown type {status} was triggered with args: {(arg1, arg2)}')
            pass

    def is_device_connected(self) -> bool:
        self.__lock.acquire()
        connected = self.__midiin is not None
        self.__lock.release()
        return connected

    def __try_connect_device(self) -> None:
        delay = 1
        previous_result = False
        while (self.__running):
            if (delay > 10.0):
                break
            portnum = get_config(MIDI_PORT_CONFIG)
            self.__lock.acquire()
            try:
                self.__midiin, _ = open_midiinput(portnum, interactive=False)
            except (NoDevicesError, InvalidPortError):
                self.__midiin = None
            except SystemError:
                pass
            self.__lock.release()
            if (self.is_device_connected() == previous_result):
                delay += 0.5
            else:
                delay = 1
            previous_result = self.is_device_connected()
            msg = f'Failed to connect to device. Trying again in {delay} seconds.' if not previous_result else f'Device connected! Checking again in {delay} seconds.'
            print(msg)
            self.__start_reading()
            sleep(delay)
        if delay > 10.0:
            print('Waited too long, stopping checking midi device')

    def __start_reading(self) -> None:
        if (self.__read_queue_thread.is_alive()
                or not self.is_device_connected()):
            return
        self.__register_callbacks()

    def __read_midi_message(self) -> tuple[int, int, int] | None:
        if not self.is_device_connected():
            return None
        self.__lock.acquire()
        msg = self.__midiin.get_message()
        self.__lock.release()
        if msg is None:
            return None
        [status, arg1, arg2] = msg[0]
        return (status, arg1, arg2)

    def __read_from_queue(self) -> None:
        while (self.__running):
            msg = self.__read_midi_message()
            if msg is None:
                continue
            status, arg1, arg2 = msg
            t = Thread(target=self.__trigger_callbacks,
                       args=(status, arg1, arg2))
            t.start()
            sleep(0.8)

    def get_midi_note(self) -> str:
        msg = self.__read_midi_message()
        if msg is None:
            return None
        status, note, velocity = msg
        self.__trigger_callbacks(status, note, velocity)
        if status != NOTE_ON or velocity == 0:
            return None
        return f'{note}'

    def get_midi_input(self) -> int:
        note = self.get_midi_note()
        midi_map: list = get_config(MIDI_CONFIG)
        try:
            return midi_map.index(f'{note}')
        except ValueError:
            return None

    def __wait_threads(self) -> None:
        if (self.__connection_thread.is_alive()):
            self.__connection_thread.join()

    def destroy(self):
        self.__running = False
        self.__wait_threads()
        if self.is_device_connected():
            self.__midiin.close_port()
        del self.__midiin
