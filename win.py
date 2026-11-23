import sys
import sounddevice as sd
import soundfile as sf
import numpy as np
from c_input import Voice
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
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, Signal, QObject
from ai import Agent
from vosk import KaldiRecognizer,Model
import json
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )

        self.model = Model("vosk-model-ar-mgb2-0.4")
        self.recognizer = KaldiRecognizer(self.model, 16000)
        self.stream = None
        self.audio = []
        self.recording = False
        self.stream = sd.RawInputStream(
            samplerate=16000,
            blocksize=8000,
            dtype="int16",
            channels=1,
            callback=self.callback,
        )
        self.Tray = QSystemTrayIcon()
        self.menu = QMenu()

        self.show_act = QAction("Show", self)
        self.hide_act = QAction("Hide", self)
        self.quit_act = QAction("Quit", self)
        self.show_act.triggered.connect(
            lambda: setattr(self, "listening", False)
        )
        self.hide_act.triggered.connect(self.listen_mode)
        self.quit_act.triggered.connect(sys.exit)

        self.menu.addAction(self.show_act)
        self.menu.addAction(self.hide_act)
        self.menu.addAction(self.quit_act)

        self.Tray.setContextMenu(self.menu)
        self.Tray.show()
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.setFixedSize(600, 185)
        self.recorder = Voice.Recorder()

        self.usermessage = QLabel("U")
        self.usermessage.setStyleSheet("color: white;")
        self.modelmessage = QLabel("M")
        self.modelmessage.setStyleSheet("color: white;")
        self.usermessage.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

        self.modelmessage.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.button = QPushButton("🎙 ابدأ التسجيل")
        self.button.clicked.connect(self.toggle_recording)
        self.exit_btn = QPushButton("X")
        self.send_btn = QPushButton("Send")
        Wlayout = QHBoxLayout()
        Rlayout = QVBoxLayout(self)
        Rlayout.addWidget(self.usermessage)
        Rlayout.addWidget(self.modelmessage)
        Rlayout.addLayout(Wlayout)
        self.exit_btn.setFixedSize(60, 20)

        self.input = QLineEdit(self)
        Wlayout.addWidget(self.exit_btn)
        Wlayout.addWidget(self.send_btn)
        Wlayout.addWidget(self.input)
        # Wlayout.addWidget(self.status)
        Wlayout.addWidget(self.button)
        self.send_btn.clicked.connect(lambda x: self.send_message())
        self.recorder.finished.connect(lambda r: self.input.setText(r))
        self.exit_btn.clicked.connect(lambda r: exit(1))

    def send_message(self):
        text = self.input.text().strip()
        self.usermessage.setText(text)
        self.input.clear()
        if not text:
            return
        print("sending...")
        Agent.send(text)
        self.modelmessage.setText(Agent.res)

    def listen_mode(self):
        self.listening=True
        self.hide()
        print("Linten mode....")
        try:
            with sd.RawInputStream(
                samplerate=Voice.SAMPLE_RATE,
                blocksize=Voice.BLOCKSIZE,
                dtype="int16",
                channels=1,
                callback=self.callback,
            ):
                while self.listening:
                    sd.sleep(1000)
            self.show()
            
            print("Linten mode end")
                    

        except KeyboardInterrupt:
            print("\nStopped.")

    def callback(self,data, frames, time, status):
        
        
        if status:
            print(status)

        if self.recognizer.AcceptWaveform(bytes(data)):
            result = json.loads(self.recognizer.Result())
            text = result.get("text", "")

            if text:
                print(text, flush=True)
                if not "خالد" ==text.split()[0]:
                    return
                self.show()
                self.listening=False
                Agent.send(text)
    def toggle_recording(self):
        if not self.recorder.recording:
            self.recorder.start()
            self.button.setText("⏹ إيقاف التسجيل")
        else:
            self.recorder.stop()
            self.button.setText("🎙 ابدأ التسجيل")
