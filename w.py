import sys
import sounddevice as sd
import soundfile as sf
import numpy as np
from c_input import Voice
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel,QHBoxLayout,QLineEdit
from PySide6.QtCore import Qt, Signal, QObject
from ai import Agent


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
        Qt.WindowType.FramelessWindowHint |
        Qt.WindowType.WindowStaysOnTopHint |
        Qt.WindowType.Tool
    )

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.setFixedSize(600,185)
        self.recorder = Voice.Recorder()

        self.status = QLabel("جاهز للتسجيل")
        self.status.isVisible=False
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.usermessage = QLabel("U")
        self.usermessage.setStyleSheet("color: white;")
        self.modelmessage = QLabel("M")
        self.modelmessage.setStyleSheet("color: white;")
        self.usermessage.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

        self.modelmessage.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.button = QPushButton("🎙 ابدأ التسجيل")
        self.button.clicked.connect(self.toggle_recording)
        self.exit_btn=QPushButton("X")
        self.send_btn=QPushButton("Send")
        Wlayout = QHBoxLayout()
        Rlayout = QVBoxLayout(self)
        Rlayout.addWidget(self.usermessage)
        Rlayout.addWidget(self.modelmessage)
        Rlayout.addLayout(Wlayout)
        self.exit_btn.setFixedSize(60,20)
        
        self.input=QLineEdit(self)
        Wlayout.addWidget(self.exit_btn)
        Wlayout.addWidget(self.send_btn)
        Wlayout.addWidget(self.input)
        # Wlayout.addWidget(self.status)
        Wlayout.addWidget(self.button)
        self.send_btn.clicked.connect(lambda x:self.send_message())
        self.recorder.finished.connect(lambda r:self.input.setText(r))
        self.exit_btn.clicked.connect(
            lambda r:exit(1)
        )

    def send_message(self):
        text = self.input.text().strip()
        self.usermessage.setText(text)
        self.input.clear()
        if not text:
            return
        print("sending...")
        Agent.send(text)
        self.modelmessage.setText(Agent.res)
        
    def toggle_recording(self):
        if not self.recorder.recording:
            self.recorder.start()
            self.button.setText("⏹ إيقاف التسجيل")
            self.status.setText("جاري التسجيل...")
        else:
            self.recorder.stop()
            self.button.setText("🎙 ابدأ التسجيل")



