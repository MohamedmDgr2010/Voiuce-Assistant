import os
import json
from tools import registry
import sys

import sys
import sounddevice as sd
import soundfile as sf
import numpy as np
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QVBoxLayout,
    QLabel,
    QHBoxLayout,
)
from PySide6.QtCore import Qt, Signal, QObject
import time as timelib

from vosk import Model, KaldiRecognizer
from agent import WorkerService

tools = registry.definitions()
from dotenv import load_dotenv
from groq import Groq
import subprocess
from openai import OpenAI

model = Model("vosk-model-ar-mgb2-0.4")
recognizer = KaldiRecognizer(model, 16000)
import re


def normalize_numbers(text):
    arabic_digits = "٠١٢٣٤٥٦٧٨٩"
    english_digits = "0123456789"

    return text.translate(str.maketrans(arabic_digits, english_digits))


class Voice:

    audio_chunks = None

    SILENCE_THRESHOLD = 500  # عدّلها حسب مستوى الميكروفون والضوضاء المحيطة
    SILENCE_DURATION = 1.0  # ثانية واحدة من الصمت بعد الكلام قبل الإرسال
    SAMPLE_RATE = 16000
    BLOCKSIZE = 12000
    STT_MODEL = None

    @staticmethod
    def is_speech(pcm_int16: np.ndarray) -> bool:
        rms = np.sqrt(np.mean(pcm_int16.astype(np.float32) ** 2))
        return rms > Voice.SILENCE_THRESHOLD

    @staticmethod
    def sttlive(indata, frames, time, status):
        global speaking, last_voice_time

        now = timelib.monotonic()
        samples = np.frombuffer(indata, dtype=np.int16)

        if Voice.is_speech(samples):
            speaking = True
            last_voice_time = now
            Voice.audio_chunks.append(bytes(indata))
        elif speaking:
            Voice.audio_chunks.append(bytes(indata))
            if (
                last_voice_time is not None
                and (now - last_voice_time) >= Voice.SILENCE_DURATION
            ):
                # اكتمل الكلام: خذ البيانات وأفرغ البافر ثم أرسل في خيط/مهمة منفصلة
                utterance = b"".join(Voice.audio_chunks)
                Voice.audio_chunks.clear()
                speaking = False
                last_voice_time = None
        if status:
            print(status)

        if recognizer.AcceptWaveform(bytes(indata)):
            result = json.loads(recognizer.Result())
            text = result.get("text", "")
            text = normalize_numbers(text)
            if text:
                print(text, flush=True)
                return text

    @staticmethod
    def stt(audio):

        audio_bytes = audio.astype(np.int16).tobytes()

        if recognizer.AcceptWaveform(audio_bytes):
            result = json.loads(recognizer.Result())
        else:
            result = json.loads(recognizer.FinalResult())

        return result.get("text", "")

    class Recorder(QObject):
        finished = Signal(str)
        voicemessage = Signal(str)

        def __init__(self):
            super().__init__()
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

        def callback(self, indata, frames, time, status):
            if status:
                print(status)

            self.audio.append(indata.copy())

        def start(self):
            self.audio = []

            self.stream = sd.InputStream(
                samplerate=16000, channels=1, dtype="int16", callback=self.callback
            )

            self.stream.start()
            self.recording = True

        def stop(self):

            if not self.recording:
                return
            print("record stop")
            self.recording = False

            self.stream.stop()

            self.stream.close()
            self.stream = None

            audio = np.concatenate(self.audio, axis=0)
            sf.write("record.wav", audio, 16000, subtype="PCM_16")
            text = normalize_numbers(Voice.stt(audio))

            self.finished.emit(text)

    class Live(QObject):
        talk = Signal(str)

        def __init__(self):
            super().__init__()
            self.listener = None
            self.listening = False
            self.audio_chunks = []

        def start(self):
            self.listener = WorkerService(self.listen)
            self.listening = True
            self.audio_chunks = []
            sd.RawOutputStream
            self.listener.start()

        def listen(self):
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

            except KeyboardInterrupt:
                print(".......................Listen mode end.............")
                self.listening = False
            except Exception as e:
                print(f"Error [listen mode] :{e}")
                self.listening = False

        def stop(self):
            self.listening = False

        def callback(self, indata, frames, time, status):

            now = timelib.monotonic()
            samples = np.frombuffer(indata, dtype=np.int16)

            if Voice.is_speech(samples):
                speaking = True
                last_voice_time = now
                self.audio_chunks.append(bytes(indata))
            elif speaking:
                self.audio_chunks.append(bytes(indata))
                if (
                    last_voice_time is not None
                    and (now - last_voice_time) >= SILENCE_DURATION
                ):
                    # اكتمل الكلام: خذ البيانات وأفرغ البافر ثم أرسل في خيط/مهمة منفصلة
                    utterance = b"".join(self.audio_chunks)
                    self.audio_chunks.clear()
                    speaking = False
                    last_voice_time = None
            if status:
                print(status)

            if recognizer.AcceptWaveform(bytes(indata)):
                result = json.loads(recognizer.Result())
                text = result.get("text", "")

                if text:
                    # print(text, flush=True)
                    self.talk.emit(text)


