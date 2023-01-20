from __future__ import annotations
from vidgear.gears import CamGear


class Section:
    def __init__(self, path: str):
        self.path = path
        self.video: CamGear = None
        self.framestamp: int = 0

    def read_frame(self):
        if self.video is None:
            return None
        frame = self.video.read()
        self.framestamp += 1
        return frame

    def seek(self, frames: int):
        if self.video is None:
            return
        for _ in range(frames):
            self.read_frame()

    def start(self, frame_offset=0) -> Section:
        if (self.path == ''):
            return None
        self.video = CamGear(source=self.path)
        self.video.start()
        self.framestamp = 0
        self.seek(frame_offset)
        return self

    def stop(self) -> None:
        if self.video is not None:
            self.video.stop()
        self.video = None
