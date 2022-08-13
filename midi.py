from rtmidi.midiutil import open_midiinput
from rtmidi.midiconstants import NOTE_OFF
from settigns import ENV


class Midi:
    NOTE_TO_SECTION: dict = ENV['NOTE_TO_SECTION']

    def __init__(self) -> None:
        portnum = ENV['MIDI_PORT']
        self.midiin, portname = open_midiinput(portnum)

    def get_midi_input(self) -> int:
        if self.midiin is None:
            return None

        msg = self.midiin.get_message()
        if msg is None:
            return None
        [status, note, velocity] = msg[0]
        if status == NOTE_OFF:
            return None
        return Midi.NOTE_TO_SECTION.get(note)

    def destroy(self):
        self.midiin.close_port()
        del self.midiin
