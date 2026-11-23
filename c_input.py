import os
import json
from tools import registry
import sys

import sys
import sounddevice as sd
import soundfile as sf
import numpy as np
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel,QHBoxLayout
from PySide6.QtCore import Qt, Signal, QObject
import time as timelib

from vosk import Model, KaldiRecognizer
tools = registry.definitions()
from dotenv import load_dotenv
from groq import Groq
import subprocess
from openai import OpenAI
model = Model("vosk-model-ar-mgb2-0.4")
recognizer = KaldiRecognizer(model, 16000)

class Voice:
    
    

    @staticmethod
    def is_speech(pcm_int16: np.ndarray) -> bool:
        rms = np.sqrt(np.mean(pcm_int16.astype(np.float32) ** 2))
        return rms > SILENCE_THRESHOLD


    @staticmethod
    def sttlive(indata, frames, time, status):
        global speaking, last_voice_time

        now = timelib.monotonic()
        samples = np.frombuffer(indata, dtype=np.int16)

        if is_speech(samples):
            speaking = True
            last_voice_time = now
            audio_chunks.append(bytes(indata))
        elif speaking:
            audio_chunks.append(bytes(indata))
            if last_voice_time is not None and (now - last_voice_time) >= SILENCE_DURATION:
                # اكتمل الكلام: خذ البيانات وأفرغ البافر ثم أرسل في خيط/مهمة منفصلة
                utterance = b"".join(audio_chunks)
                audio_chunks.clear()
                speaking = False
                last_voice_time = None
        if status:
            print(status)

        if recognizer.AcceptWaveform(bytes(indata)):
            result = json.loads(recognizer.Result())
            text = result.get("text", "")

            if text:
                print(text, flush=True)
                exe(text)
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
        voicemessage=Signal(str)
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
        callback=self.callback
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
            text=Voice.stt(audio)

            self.finished.emit(text)
