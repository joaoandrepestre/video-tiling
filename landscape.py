from vidgear.gears import CamGear
from ffpyplayer.player import MediaPlayer

class Landscape:
    def __init__(self, paths: list[str]) -> None:
        self.paths: list[str] = paths
        self.sections: list[CamGear] = [None for i in range(len(paths))]
        self.audios: list[MediaPlayer] = [None for i in range(len(paths))]

    def start_section(self, idx: int) -> CamGear:
        path = self.paths[idx]
        if (path == ''): return None
        self.sections[idx] = CamGear(source=path)
        video = self.sections[idx]
        video.start()
        self.audios[idx] = MediaPlayer(path)
        return video

    def stop_section(self, idx: int) -> None:
        section = self.sections[idx]
        if section is not None:
            section.stop()
        self.sections[idx] = None

        audio = self.audios[idx]
        if audio is not None:
            audio.set_mute(True)
            audio.close_player()
        self.audios[idx] = None
