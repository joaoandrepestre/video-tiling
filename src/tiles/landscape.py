from tiles.section import Section
from ffpyplayer.player import MediaPlayer


class Landscape:
    def __init__(self, paths: list[str]) -> None:
        self.sections: list[Section] = [Section(path) for path in paths]
        self.audio_path = paths[0]
        self.audio: MediaPlayer = None
        self.playing_sections: int = 0

    def framestamp(self) -> int:
        return max([s.framestamp for s in self.sections])

    def start_audio(self) -> None:
        if (self.audio is None):
            self.audio = MediaPlayer(self.audio_path)

    def stop_audio(self) -> None:
        if (self.audio is not None):
            print('stopping audio')
            self.audio.set_mute(True)
            self.audio.close_player()
            self.audio = None

    def start_section(self, idx: int, resume: bool = False) -> Section:
        self.playing_sections += 1
        if (self.audio is None):
            self.start_audio()
        if not resume:
            return self.sections[idx].start()
        else:
            return self.sections[idx].start(self.framestamp())

    def stop_section(self, idx: int) -> None:
        self.playing_sections -= 1
        if (self.playing_sections == 0):
            self.stop_audio()
        return self.sections[idx].stop()

    def restart_section(self, idx: int) -> Section:
        self.stop_section(idx)
        return self.start_section(idx)

    def get_frame(self, idx: int):
        if (self.audio is not None):
            _, val = self.audio.get_frame(show=False)
            if val == 'eof':
                self.stop_audio()
        return self.sections[idx].read_frame()
