from __future__ import annotations

import math
from datetime import datetime

from PySide6.QtCore import QPoint, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from hermes_bridge.ui.assets import resolve_asset_path


def should_hide_instead_of_close(voice_mode_enabled: bool) -> bool:
    return voice_mode_enabled


class HermesCoreWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._logo = QPixmap(str(resolve_asset_path("hermes-logo.png")))
        self.setMinimumSize(230, 230)

    def paintEvent(self, event) -> None:  # noqa: N802
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect().adjusted(12, 12, -12, -12)
        center = rect.center()
        radius = min(rect.width(), rect.height()) / 2

        for index, alpha in enumerate((230, 120, 70, 45)):
            pen = QPen(QColor(245, 245, 245, alpha), 1)
            painter.setPen(pen)
            inset = index * 18
            painter.drawEllipse(QRectF(rect).adjusted(inset, inset, -inset, -inset))

        painter.setPen(QPen(QColor(255, 255, 255, 220), 2))
        corner = 28
        painter.drawLine(rect.left(), rect.top(), rect.left() + corner, rect.top())
        painter.drawLine(rect.left(), rect.top(), rect.left(), rect.top() + corner)
        painter.drawLine(rect.right(), rect.top(), rect.right() - corner, rect.top())
        painter.drawLine(rect.right(), rect.top(), rect.right(), rect.top() + corner)
        painter.drawLine(
            rect.left(), rect.bottom(), rect.left() + corner, rect.bottom()
        )
        painter.drawLine(
            rect.left(), rect.bottom(), rect.left(), rect.bottom() - corner
        )
        painter.drawLine(
            rect.right(), rect.bottom(), rect.right() - corner, rect.bottom()
        )
        painter.drawLine(
            rect.right(), rect.bottom(), rect.right(), rect.bottom() - corner
        )

        logo_size = int(radius * 0.86)
        logo_rect = QRectF(
            center.x() - logo_size / 2,
            center.y() - logo_size / 2,
            logo_size,
            logo_size,
        )
        if not self._logo.isNull():
            painter.drawPixmap(logo_rect.toRect(), self._logo)
        else:
            painter.setPen(QColor(255, 255, 255))
            font = QFont("Consolas", 54, QFont.Bold)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignCenter, "H")

        painter.setPen(QColor(190, 190, 190, 150))
        painter.setFont(QFont("Consolas", 11, QFont.Bold))
        painter.drawText(
            QRectF(center.x() - radius, center.y() + 45, radius * 2, 30),
            Qt.AlignCenter,
            "HERMES",
        )


class WaveformWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._phase = 0.0
        self.setMinimumHeight(40)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(90)

    def _tick(self) -> None:
        self._phase += 0.32
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor(255, 255, 255), 2))

        width = self.width()
        height = self.height()
        bars = 31
        gap = 5
        bar_width = 2
        total_width = bars * bar_width + (bars - 1) * gap
        start_x = (width - total_width) / 2

        for index in range(bars):
            wave = math.sin(self._phase + index * 0.55)
            bar_height = 8 + abs(wave) * 24
            x = start_x + index * (bar_width + gap)
            y = (height - bar_height) / 2
            painter.drawLine(int(x), int(y), int(x), int(y + bar_height))


class HermesMainWindow(QMainWindow):
    command_submitted = Signal(str)
    voice_pressed = Signal()
    voice_released = Signal()
    voice_mode_toggled = Signal(bool)

    def __init__(self, tts_enabled: bool = True) -> None:
        super().__init__()
        self._drag_position: QPoint | None = None
        self._tts_enabled = tts_enabled
        self._tts_unavailable_reported = False
        self._voice_mode_enabled = False
        self._speech = self._create_speech_engine()
        self.setWindowTitle("Hermes Voice Bridge")
        self.setMinimumSize(820, 560)
        self.resize(900, 620)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._clock = QLabel()
        self._clock.setObjectName("Clock")
        self._status = QLabel("HERMES . OFFLINE")
        self._status.setObjectName("Status")
        self._conversation = QTextEdit()
        self._system_log = QTextEdit()
        self._input = QLineEdit()
        self._hold_button = QPushButton("HOLD TO TALK")
        self._voice_mode_button = QPushButton("VOICE MODE OFF")

        self._build_ui()
        self._start_clock()

    def set_status(self, status: str) -> None:
        self._status.setText(f"HERMES . {status}")
        self.append_system(f"SYS: Status changed to {status}")

    def append_user_command(self, command: str) -> None:
        self._append_conversation("USER", command)

    def append_hermes_reply(self, message: str) -> None:
        self._append_conversation("HERMES", message)
        self.speak_hermes_reply(message)

    def append_system(self, message: str) -> None:
        self._system_log.append(message)

    def set_tts_enabled(self, enabled: bool) -> None:
        self._tts_enabled = enabled

    def speak_hermes_reply(self, message: str) -> None:
        text = message.strip()
        if not self._tts_enabled or not text:
            return
        if self._speech is None:
            if not self._tts_unavailable_reported:
                self._tts_unavailable_reported = True
                self.append_system("SYS: Text-to-speech is unavailable on this system.")
            return
        self._speech.stop()
        self._speech.say(text)

    def keep_command_for_retry(self, message: str) -> None:
        self.append_system(message)

    def submit_voice_transcript(self, transcript: str) -> None:
        command = transcript.strip()
        if not command:
            self.append_system("SYS: Voice transcript was empty.")
            return
        self.append_system(f"SYS: Voice transcript: {command}")
        self.append_user_command(command)
        self.command_submitted.emit(command)

    def set_voice_ready(self) -> None:
        self._hold_button.setEnabled(True)
        self._hold_button.setText("HOLD TO TALK")
        self.set_status("READY")

    def set_voice_mode_enabled(self, enabled: bool) -> None:
        self._voice_mode_enabled = enabled
        self._voice_mode_button.blockSignals(True)
        self._voice_mode_button.setChecked(enabled)
        self._voice_mode_button.blockSignals(False)
        self._voice_mode_button.setText(
            "VOICE MODE ON" if enabled else "VOICE MODE OFF"
        )
        self.append_system(
            "SYS: Voice mode enabled." if enabled else "SYS: Voice mode disabled."
        )

    def show_activated(self) -> None:
        if self.isMinimized():
            self.showNormal()
        else:
            self.show()
        self.raise_()
        self.activateWindow()

    def set_voice_disabled(self) -> None:
        self._hold_button.setEnabled(False)
        self._hold_button.setText("VOICE OFFLINE")

    def set_voice_listening(self) -> None:
        self._hold_button.setEnabled(True)
        self._hold_button.setText("RELEASE TO SEND")
        self.set_status("LISTENING")

    def set_voice_transcribing(self) -> None:
        self._hold_button.setEnabled(False)
        self._hold_button.setText("TRANSCRIBING")
        self.set_status("THINKING")

    def set_voice_error(self, message: str) -> None:
        self.append_system(f"SYS: {message}")
        self.set_voice_ready()

    def _create_speech_engine(self):
        if not self._tts_enabled:
            return None
        try:
            from PySide6.QtTextToSpeech import QTextToSpeech
        except Exception:
            return None
        return QTextToSpeech(self)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton:
            self._drag_position = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if event.buttons() == Qt.LeftButton and self._drag_position is not None:
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()

    def closeEvent(self, event) -> None:  # noqa: N802
        if should_hide_instead_of_close(self._voice_mode_enabled):
            event.ignore()
            self.hide()
            self.append_system("SYS: Window hidden; voice mode still listening.")
            return
        super().closeEvent(event)

    def _build_ui(self) -> None:
        shell = QFrame()
        shell.setObjectName("Shell")
        self.setCentralWidget(shell)

        root = QVBoxLayout(shell)
        root.setContentsMargins(22, 20, 22, 14)
        root.setSpacing(16)

        root.addLayout(self._header())

        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(14)
        grid.addWidget(self._left_panel(), 0, 0)
        grid.addWidget(self._right_panel(), 0, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        root.addLayout(grid, stretch=1)

        root.addLayout(self._footer())

    def _header(self) -> QHBoxLayout:
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(1)

        title = QLabel("H.E.R.M.E.S")
        title.setObjectName("Title")
        subtitle = QLabel("HERMES EXECUTION & RESPONSE MODULE")
        subtitle.setObjectName("Subtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        header.addLayout(title_box)
        header.addStretch(1)
        header.addWidget(self._clock)

        minimize = QPushButton("-")
        minimize.setObjectName("WindowButton")
        minimize.clicked.connect(self.showMinimized)
        close = QPushButton("x")
        close.setObjectName("WindowButton")
        close.clicked.connect(self.close)

        header.addWidget(minimize)
        header.addWidget(close)
        return header

    def _left_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        core = HermesCoreWidget()
        layout.addWidget(core, alignment=Qt.AlignCenter)
        layout.addWidget(self._status, alignment=Qt.AlignCenter)
        layout.addWidget(WaveformWidget())

        system_panel = QFrame()
        system_panel.setObjectName("Panel")
        system_layout = QVBoxLayout(system_panel)
        system_layout.setContentsMargins(12, 10, 12, 10)
        label = QLabel("SYSTEM")
        label.setObjectName("SectionTitle")
        self._system_log.setReadOnly(True)
        self._system_log.setMinimumHeight(90)
        system_layout.addWidget(label)
        system_layout.addWidget(self._system_log)
        layout.addWidget(system_panel)

        self._hold_button.setEnabled(True)
        self._hold_button.pressed.connect(self.voice_pressed.emit)
        self._hold_button.released.connect(self.voice_released.emit)
        layout.addWidget(self._hold_button)

        self._voice_mode_button.setCheckable(True)
        self._voice_mode_button.toggled.connect(self._toggle_voice_mode)
        layout.addWidget(self._voice_mode_button)
        return panel

    def _right_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("Panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        label = QLabel("CONVERSATION LOG")
        label.setObjectName("SectionTitle")
        self._conversation.setReadOnly(True)
        self._conversation.setMinimumWidth(360)

        input_row = QHBoxLayout()
        self._input.setPlaceholderText(">")
        self._input.returnPressed.connect(self._submit_command)
        send = QPushButton("SEND")
        send.clicked.connect(self._submit_command)
        input_row.addWidget(self._input, stretch=1)
        input_row.addWidget(send)

        layout.addWidget(label)
        layout.addWidget(self._conversation, stretch=1)
        layout.addLayout(input_row)
        return panel

    def _footer(self) -> QHBoxLayout:
        footer = QHBoxLayout()
        left = QLabel("OpenJarvis Industries")
        center = QLabel("MODEL hermes-0.5")
        right = QLabel("AGENT HERMES")
        for label in (left, center, right):
            label.setObjectName("Footer")
        footer.addWidget(left)
        footer.addStretch(1)
        footer.addWidget(center)
        footer.addStretch(1)
        footer.addWidget(right)
        return footer

    def _start_clock(self) -> None:
        timer = QTimer(self)
        timer.timeout.connect(self._update_clock)
        timer.start(1000)
        self._update_clock()

    def _update_clock(self) -> None:
        self._clock.setText(datetime.now().strftime("%I:%M:%S %p"))

    def _toggle_voice_mode(self, enabled: bool) -> None:
        self._voice_mode_button.setText(
            "VOICE MODE ON" if enabled else "VOICE MODE OFF"
        )
        self.voice_mode_toggled.emit(enabled)

    def _submit_command(self) -> None:
        command = self._input.text().strip()
        if not command:
            return
        self._input.clear()
        self.append_user_command(command)
        self.command_submitted.emit(command)

    def _append_conversation(self, speaker: str, message: str) -> None:
        self._conversation.append(f"{speaker}: {message}")
