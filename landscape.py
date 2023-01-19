from section import Section


class Landscape:
    def __init__(self, paths: list[str]) -> None:
        self.sections: list[Section] = [Section(path) for path in paths]

    def framestamp(self) -> int:
        return max([s.framestamp for s in self.sections])

    def start_section(self, idx: int, resume: bool = False) -> Section:
        if not resume:
            return self.sections[idx].start()
        else:
            return self.sections[idx].start(self.framestamp())

    def stop_section(self, idx: int) -> None:
        return self.sections[idx].stop()
