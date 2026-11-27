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
    QFrame,
    QGraphicsDropShadowEffect,
    QTextEdit,
)
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPen, QPixmap, QPolygon
from PySide6.QtCore import Qt, QRect, Signal, QObject, QEvent, QPoint, QSize, QTimer
from agent import Agent, WorkerService
from vosk import KaldiRecognizer, Model
import json


class MessageBubble(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 18, 10, 0)

        card = QFrame(self)
        card.setObjectName("Card")
        outer.addWidget(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)

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
        self.modelmessage.document().setDefaultStyleSheet("""
            body, p, li { color: #eaf6ef; }
            a { color: #7aa2f7; }
            h1, h2, h3, h4, h5, h6 { color: #ffffff; }
            pre { background-color: #16161d; color: #eaf6ef; border-radius: 6px; }
            code { background-color: #16161d; color: #f0b7c5; }
            blockquote { color: #b9c7d9; border-left: 3px solid #5a8ae8; }
            """)
        self.modelmessage.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        layout.addWidget(self.modelmessage)

    def fit(self, width):
        self.setFixedWidth(width)
        doc = self.modelmessage.document()
        doc.setTextWidth(width - 48)
        height = int(doc.size().height()) + 58
        self.setFixedHeight(max(90, min(height, 460)))


class MainWindow(QWidget):
    BUBBLE_GAP = 5
    TASKBAR_GAP = 15

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
        QPushButton#SoundCheck {
            background: transparent;
            border: none;
            padding: 0px;
        }
        QPushButton#SoundCheck:hover {
            background: #4a4a58;
        }
    """

    @staticmethod
    def make_icon(kind, color):
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(color))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        if kind == "mic":
            painter.drawRoundedRect(QRect(12, 5, 8, 14), 4, 4)
            painter.drawArc(QRect(9, 11, 14, 12), 0, 180 * 16)
            painter.drawLine(16, 23, 16, 28)
            painter.drawLine(12, 28, 20, 28)
        elif kind == "stop":
            painter.setBrush(QColor(color))
            painter.drawRoundedRect(QRect(10, 10, 12, 12), 2, 2)
        elif kind == "send":
            painter.drawPolygon(
                QPolygon(
                    [
                        QPoint(5, 16),
                        QPoint(27, 6),
                        QPoint(20, 26),
                        QPoint(16, 18),
                        QPoint(5, 16),
                    ]
                )
            )
            painter.drawLine(16, 18, 27, 6)
        elif kind in ("sound_on", "sound_off"):
            painter.setBrush(QColor(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPolygon(
                QPolygon(
                    [
                        QPoint(5, 13),
                        QPoint(10, 13),
                        QPoint(16, 8),
                        QPoint(16, 24),
                        QPoint(10, 19),
                        QPoint(5, 19),
                    ]
                )
            )
            if kind == "sound_on":
                painter.setBrush(Qt.BrushStyle.NoBrush)
                pen.setWidth(2)
                painter.setPen(pen)
                painter.drawArc(QRect(18, 11, 8, 10), -60 * 16, 120 * 16)
                painter.drawArc(QRect(21, 7, 13, 18), -60 * 16, 120 * 16)
            else:
                pen.setWidth(2)
                painter.setPen(pen)
                painter.drawLine(21, 12, 28, 20)
                painter.drawLine(28, 12, 21, 20)
        elif kind == "close":
            painter.drawLine(10, 10, 22, 22)
            painter.drawLine(22, 10, 10, 22)

        painter.end()
        return QIcon(pixmap)

    @staticmethod
    def workarea_bottom():
        screen = QApplication.primaryScreen()
        available = screen.availableGeometry()
        if available.bottom() < screen.geometry().bottom():
            return available.bottom()
        probe = QWidget()
        probe.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        probe.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        probe.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        probe.showMaximized()
        QApplication.processEvents()
        bottom = probe.geometry().bottom()
        probe.close()
        probe.deleteLater()
        return bottom

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setFixedSize(600, 85)
        # 
        
        screen = QApplication.primaryScreen()
        geometry = screen.geometry()
        bottom = self.workarea_bottom()
        x = geometry.x() + (geometry.width() - self.width()) // 2
        y = bottom - self.height() - self.TASKBAR_GAP
        self.home_pos = QPoint(x, y)
        self.move(self.home_pos)

        self.sound = False

        self.sound_on_icon = self.make_icon("sound_on", "#d8d8e0")
        self.sound_off_icon = self.make_icon("sound_off", "#d8d8e0")

        self.check_sound = QPushButton()
        self.check_sound.setObjectName("SoundCheck")
        self.check_sound.setCheckable(True)
        self.check_sound.setIcon(self.sound_off_icon)
        self.check_sound.setIconSize(QSize(18, 18))
        self.check_sound.setToolTip("الصوت")
        self.check_sound.setFixedSize(32, 32)
        self.check_sound.toggled.connect(self.on_sound_toggled)
        self.show_show_message_worker = None
        self.stream = None
        self.audio = []
        self.recording = False

        
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(self.STYLE_SHEET)

        self.bubble = MessageBubble()
        self.bubble.setStyleSheet(self.STYLE_SHEET)
        self.modelmessage = self.bubble.modelmessage
        QApplication.instance().installEventFilter(self)
        QApplication.instance().applicationStateChanged.connect(self.on_app_state)

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

        self.taskBar = QWidget()

        Wlayout = QHBoxLayout(self.taskBar)
        Wlayout.setContentsMargins(0, 0, 0, 0)
        Wlayout.setSpacing(8)
        Rlayout.addWidget(self.taskBar)

        self.record_icon = self.make_icon("mic", "#ffffff")
        self.stop_icon = self.make_icon("stop", "#ffffff")

        self.button = QPushButton()
        self.button.setObjectName("RecordButton")
        self.button.setIcon(self.record_icon)
        self.button.setIconSize(QSize(18, 18))
        self.button.setToolTip("ابدأ التسجيل")
        self.button.setFixedSize(40, 32)
        self.button.clicked.connect(self.toggle_recording)

        self.exit_btn = QPushButton()
        self.exit_btn.setObjectName("ExitButton")
        self.exit_btn.setIcon(self.make_icon("close", "#b9b9c4"))
        self.exit_btn.setIconSize(QSize(14, 14))
        self.exit_btn.setToolTip("إغلاق")
        self.exit_btn.setFixedSize(26, 26)

        self.send_btn = QPushButton()
        self.send_btn.setObjectName("SendButton")
        self.send_btn.setIcon(self.make_icon("send", "#ffffff"))
        self.send_btn.setIconSize(QSize(20, 20))
        self.send_btn.setToolTip("إرسال")
        self.send_btn.setFixedSize(40, 32)

        self.input = QLineEdit()
        self.input.setObjectName("Input")

        Wlayout.addWidget(self.exit_btn)
        Wlayout.addWidget(self.send_btn)
        Wlayout.addWidget(self.input)
        Wlayout.addWidget(self.check_sound)
        Wlayout.addWidget(self.button)

        self.send_btn.clicked.connect(lambda x: self.send_message())
        self.recorder.finished.connect(lambda r: self.input.setText(r))
        self.exit_btn.clicked.connect(lambda r: sys.exit(1))

    def send_message(self):
        text = self.input.text().strip()

        if not text:
            return
        self.bubble.hide()
        # timelib.sleep(1)
        print("sending...")
        self.input.clear()
        worker = WorkerService(Agent.send, text=text)
        worker.finished.connect(self.show_model_message)
        self.show_show_message_worker = worker
        self.show_show_message_worker.start()

    def set_markdown(self, text):
        self.modelmessage.setMarkdown(text or "")

    def on_sound_toggled(self, checked):
        self.check_sound.setIcon(self.sound_on_icon if checked else self.sound_off_icon)
        self.check_sound.setToolTip("الصوت" if checked else "بدون صوت")

    def show_model_message(self, t):
        print("show model message")
        self.set_markdown(Agent.res)
        self.bubble.fit(self.width())
        top_left = self.pos()
        self.bubble_pos = QPoint(
            top_left.x(), top_left.y() - self.bubble.height() - self.BUBBLE_GAP
        )
        self.bubble.show()
        QTimer.singleShot(0, self.apply_bubble_pos)
        self.raise_()
        if self.check_sound.isChecked():
            self.sound_worker = WorkerService(Agent.speek, text=Agent.res)
            self.sound_worker.start()

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.MouseButtonPress and self.bubble.isVisible():
            pos = event.globalPosition().toPoint()
            inside_window = self.geometry().contains(pos)
            inside_bubble = self.bubble.geometry().contains(pos)
            if not inside_window and not inside_bubble:
                self.bubble.hide()
        return super().eventFilter(watched, event)

    def on_app_state(self, state):
        if state != Qt.ApplicationState.ApplicationActive:
            self.bubble.hide()
            self.raise_()
            self.activateWindow()

    def apply_bubble_pos(self):
        if self.bubble.isVisible():
            self.bubble.move(self.bubble_pos)

    def apply_home_pos(self):
        self.move(self.home_pos)

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self.apply_home_pos)

    def hideEvent(self, event):
        self.bubble.hide()
        super().hideEvent(event)

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
            self.button.setIcon(self.stop_icon)
            self.button.setToolTip("إيقاف التسجيل")
        else:
            self.recorder.stop()
            self.button.setIcon(self.record_icon)
            self.button.setToolTip("ابدأ التسجيل")
