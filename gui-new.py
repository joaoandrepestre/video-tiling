import sys
import threading
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton
from midi import Midi
import tile as T

WIDTH = 450
HEIGHT = 600


class Window(QWidget):
    def __init__(self, midi: Midi) -> None:
        super().__init__()
        self.render_thread: threading.Thread = None

        self.resize(WIDTH, HEIGHT)

        self.button = QPushButton("Start", self)
        self.button.clicked.connect(lambda: self.start_callback(midi))

    def is_rendering(self) -> bool:
        return self.render_thread is not None and self.render_thread.is_alive()

    def start_callback(self, midi: Midi) -> None:
        if (not self.is_rendering()):
            self.render_thread = threading.Thread(
                group=None, target=T.render, args=[midi])
            self.render_thread.start()


app = QApplication(sys.argv)
midi = Midi()
window = Window(midi)
window.show()
sys.exit(app.exec())
