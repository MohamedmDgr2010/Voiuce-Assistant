import sys
import sounddevice as sd
import soundfile as sf
import numpy as np
import time as timelib
from voice import Voice
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QVBoxLayout,
    QLabel,
    QHBoxLayout,
    QLineEdit,
    QSystemTrayIcon,
    QMenu,
    QCheckBox,
    QFrame,
    QGraphicsDropShadowEffect,
    QTextEdit,
)
from PySide6.QtGui import QAction, QColor
from PySide6.QtCore import Qt, Signal, QObject
from agent import Agent, WorkerService
from vosk import KaldiRecognizer, Model
import json


class MainWindow(QWidget):
    STYLE_SHEET = """
        QWidget#Card {
            background: #202028;
            border: 1px solid #3a3a46;
            border-radius: 16px;
        }
        QLabel#UserMessage {
            background: #2c3e55;
            color: #eaf1fb;
            border-radius: 10px;
            padding: 8px 12px;
            font-size: 14px;
        }
        QTextEdit#ModelMessage {
            background: #2b3c35;
            color: #eaf6ef;
            border: none;
            border-radius: 10px;
            font-size: 14px;
            selection-background-color: #5b7cfa;
        }
        QLineEdit#Input {
            background: #16161d;
            color: #f2f2f6;
            border: 1px solid #4a4a56;
            border-radius: 10px;
            padding: 6px 12px;
            font-size: 14px;
            selection-background-color: #5b7cfa;
        }
        QLineEdit#Input:focus {
            border: 1px solid #7aa2f7;
        }
        QPushButton {
            background: #3a3a46;
            color: #f5f5f7;
            border: 1px solid #50505c;
            border-radius: 10px;
            padding: 6px 12px;
            font-size: 13px;
        }
        QPushButton:hover {
            background: #4a4a58;
        }
        QPushButton:pressed {
            background: #2d2d37;
        }
        QPushButton#RecordButton {
            background: #c9474f;
            border-color: #e06169;
            font-weight: bold;
        }
        QPushButton#RecordButton:hover {
            background: #d9535b;
        }
        QPushButton#SendButton {
            background: #3d6fd1;
            border-color: #5a8ae8;
            font-weight: bold;
        }
        QPushButton#SendButton:hover {
            background: #477ee0;
        }
        QPushButton#ExitButton {
            background: transparent;
            border: none;
            color: #b9b9c4;
            font-size: 16px;
            padding: 0px;
        }
        QPushButton#ExitButton:hover {
            color: #ff6b6b;
        }
        QCheckBox#SoundCheck {
            color: #d8d8e0;
            spacing: 6px;
        }
        QCheckBox#SoundCheck::indicator {
            width: 16px;
            height: 16px;
            border: 1px solid #6b6b78;
            border-radius: 4px;
            background: #16161d;
        }
        QCheckBox#SoundCheck::indicator:checked {
            background: #3d6fd1;
            border-color: #5a8ae8;
        }
    """

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )

        self.setFixedSize(600, 185)
        screen = QApplication.primaryScreen().availableGeometry()

        x = screen.x() + (screen.width() - self.width()) // 2
        y = screen.y() + screen.height() - self.height()

        self.move(x, y)
        self.sound = False

        self.check_sound = QCheckBox("sound")
        self.check_sound.setObjectName("SoundCheck")
        self.show_show_message_worker = None
        self.stream = None
        self.audio = []
        self.recording = False

        self.Tray = QSystemTrayIcon()
        self.menu = QMenu()

        self.show_act = QAction("Show", self)
        self.hide_act = QAction("Hide", self)
        self.quit_act = QAction("Quit", self)

        self.show_act.triggered.connect(lambda: setattr(self, "listening", False))
        self.hide_act.triggered.connect(self.listen_mode)
        self.quit_act.triggered.connect(sys.exit)

        self.menu.addAction(self.show_act)
        self.menu.addAction(self.hide_act)
        self.menu.addAction(self.quit_act)

        self.Tray.setContextMenu(self.menu)
        self.Tray.show()
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(self.STYLE_SHEET)

        self.recorder = Voice.Recorder()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 10, 10, 14)

        self.card = QFrame(self)
        self.card.setObjectName("Card")
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(18)
        shadow.setColor(QColor(0, 0, 0, 170))
        shadow.setOffset(0, 4)
        self.card.setGraphicsEffect(shadow)
        outer.addWidget(self.card)

        Rlayout = QVBoxLayout(self.card)
        Rlayout.setContentsMargins(14, 12, 14, 12)
        Rlayout.setSpacing(8)

        
        self.modelmessage = QTextEdit()
        self.modelmessage.setObjectName("ModelMessage")
        self.modelmessage.setReadOnly(True)
        self.modelmessage.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextBrowserInteraction
        )
        self.modelmessage.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.modelmessage.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.modelmessage.document().setDocumentMargin(8)
        self.modelmessage.document().setDefaultStyleSheet(
            """
            body, p, li { color: #eaf6ef; }
            a { color: #7aa2f7; }
            h1, h2, h3, h4, h5, h6 { color: #ffffff; }
            pre { background-color: #16161d; color: #eaf6ef; border-radius: 6px; }
            code { background-color: #16161d; color: #f0b7c5; }
            blockquote { color: #b9c7d9; border-left: 3px solid #5a8ae8; }
            """
        )

       
        self.modelmessage.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        Rlayout.addWidget(self.modelmessage)
        Rlayout.setStretch(0, 1)
        Rlayout.setStretch(1, 1)

        self.taskBar = QWidget()
        Wlayout = QHBoxLayout(self.taskBar)
        Wlayout.setContentsMargins(0, 0, 0, 0)
        Wlayout.setSpacing(8)
        Rlayout.addWidget(self.taskBar)

        self.button = QPushButton("🎙 ابدأ التسجيل")
        self.button.setObjectName("RecordButton")
        self.button.clicked.connect(self.toggle_recording)

        self.exit_btn = QPushButton("X")
        self.exit_btn.setObjectName("ExitButton")
        self.exit_btn.setFixedSize(26, 26)

        self.send_btn = QPushButton("Send")
        self.send_btn.setObjectName("SendButton")

        self.input = QLineEdit()
        self.input.setObjectName("Input")

        Wlayout.addWidget(self.exit_btn)
        Wlayout.addWidget(self.send_btn)
        Wlayout.addWidget(self.input)
        Wlayout.addWidget(self.check_sound)
        Wlayout.addWidget(self.button)

        self.send_btn.clicked.connect(lambda x: self.send_message())
        self.recorder.finished.connect(lambda r: self.input.setText(r))
        self.exit_btn.clicked.connect(lambda r: exit(1))

    def send_message(self):
        text = self.input.text().strip()

        if not text:
            return
        # timelib.sleep(1)
        self.set_markdown("التفكير...")
        print("sending...")
        self.input.clear()
        worker = WorkerService(Agent.send, text=text)
        worker.finished.connect(self.show_model_message)
        self.show_show_message_worker = worker
        self.show_show_message_worker.start()

    def set_markdown(self, text):
        self.modelmessage.setMarkdown(text or "")

    def show_model_message(self, t):
        print("show model message")
        self.set_markdown(Agent.res)
        if self.check_sound.isChecked():
            self.sound_worker = WorkerService(Agent.speek, text=Agent.res)
            self.sound_worker.start()

    def listen_mode(self):
        self.listening = True
        self.hide()
        print("Linten mode....")
        try:
            timelib.sleep(5)
            self.show()
        
        except Exception as e:
            print(f"[LISTEN_MODE] Error: {e}")

    def toggle_recording(self):
        if not self.recorder.recording:
            self.recorder.start()
            self.button.setText("⏹ إيقاف التسجيل")
        else:
            self.recorder.stop()
            self.button.setText("🎙 ابدأ التسجيل")
