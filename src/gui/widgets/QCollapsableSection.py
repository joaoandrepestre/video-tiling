from PyQt6.QtWidgets import QWidget, QToolButton, QScrollArea, QVBoxLayout, QSizePolicy, QFrame
from PyQt6.QtCore import Qt, QParallelAnimationGroup, QPropertyAnimation, QAbstractAnimation


class QCollapsableSection(QWidget):
    def __init__(self, title: str):
        super().__init__()
        self.toggle_button = QToolButton()
        self.toggle_button.setText(title)
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(False)
        self.toggle_button.setStyleSheet('border: none;')
        self.toggle_button.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        )
        self.toggle_button.setArrowType(Qt.ArrowType.RightArrow)
        self.toggle_button.clicked.connect(self.__on_pressed)

        self.toggle_animation = QParallelAnimationGroup(self)

        self.content_area = QScrollArea()
        self.content_area.setMinimumWidth(450)
        self.content_area.setMaximumHeight(0)
        self.content_area.setMinimumHeight(0)
        self.content_area.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.content_area.setFrameShape(QFrame.Shape.NoFrame)

        vbox = QVBoxLayout(self)
        vbox.setSpacing(0)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.addWidget(self.toggle_button)
        vbox.addWidget(self.content_area)

        self.toggle_animation.addAnimation(
            QPropertyAnimation(self, b'minimumHeight'))
        self.toggle_animation.addAnimation(
            QPropertyAnimation(self, b'maximumHeight'))
        self.toggle_animation.addAnimation(
            QPropertyAnimation(self.content_area, b'maximumHeight'))

    def check(self):
        self.toggle_button.clicked.emit()

    def __on_pressed(self):
        checked = self.toggle_button.isChecked()
        self.toggle_button.setArrowType(
            Qt.ArrowType.DownArrow if not checked else Qt.ArrowType.RightArrow
        )
        self.toggle_animation.setDirection(
            QAbstractAnimation.Direction.Forward
            if not checked
            else QAbstractAnimation.Direction.Backward
        )
        self.toggle_animation.start()

    def setContentLayout(self, layout):
        lay = self.content_area.layout()
        del lay
        self.content_area.setLayout(layout)
        collapsed_height = (
            self.sizeHint().height() - self.content_area.maximumHeight()
        )
        content_height = layout.sizeHint().height()
        for i in range(self.toggle_animation.animationCount()):
            animation = self.toggle_animation.animationAt(i)
            animation.setDuration(500)
            animation.setStartValue(collapsed_height)
            animation.setEndValue(collapsed_height + content_height)

        content_animation = self.toggle_animation.animationAt(
            self.toggle_animation.animationCount() - 1
        )
        content_animation.setDuration(500)
        content_animation.setStartValue(0)
        content_animation.setEndValue(content_height)
