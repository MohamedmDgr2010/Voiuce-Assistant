# import json

# import time as timelib
# import sounddevice as sd
# import json
# from vosk import Model, KaldiRecognizer
# from agentimport send
# import numpy as np
# from voice import Voice
# MODEL_PATH = "./vosk-model-ar-mgb2-0.4"
# SAMPLE_RATE = 16000
# BLOCKSIZE = 1024*12  # ~64ms لكل بلوك عند 16kHz
# SILENCE_THRESHOLD = 500  # عدّلها حسب مستوى الميكروفون والضوضاء المحيطة
# SILENCE_DURATION = 1.0  # ثانية واحدة من الصمت بعد الكلام قبل الإرسال
# audio_chunks = []
# speaking = False
# last_voice_time = None

# print("Loading Arabic speech model...")
# model = Model(MODEL_PATH)
# recognizer = KaldiRecognizer(model, SAMPLE_RATE)

# print("Listening... Speak now (Ctrl+C to stop)\n")


# # def is_speech(pcm_int16: np.ndarray) -> bool:
# #     rms = np.sqrt(np.mean(pcm_int16.astype(np.float32) ** 2))
# #     return rms > SILENCE_THRESHOLD


# # def callback(indata, frames, time, status):
# #     global speaking, last_voice_time

# #     now = timelib.monotonic()
# #     samples = np.frombuffer(indata, dtype=np.int16)

# #     if is_speech(samples):
# #         speaking = True
# #         last_voice_time = now
# #         audio_chunks.append(bytes(indata))
# #     elif speaking:
# #         audio_chunks.append(bytes(indata))
# #         if last_voice_time is not None and (now - last_voice_time) >= SILENCE_DURATION:
# #             # اكتمل الكلام: خذ البيانات وأفرغ البافر ثم أرسل في خيط/مهمة منفصلة
# #             utterance = b"".join(audio_chunks)
# #             audio_chunks.clear()
# #             speaking = False
# #             last_voice_time = None
# #     if status:
# #         print(status)

# #     if recognizer.AcceptWaveform(bytes(indata)):
# #         result = json.loads(recognizer.Result())
# #         text = result.get("text", "")

# #         if text:
# #             print(text, flush=True)
# #             exe(text)

# #     # else:
# #     #     partial = json.loads(recognizer.PartialResult())
# #     #     text = partial.get("partial", "")

# #     #     if text:
# #     #         print("\r" + text + " " * 20, end="", flush=True)


# def exe(text: str) -> None:
#     send(text)


# try:
#     with sd.RawInputStream(
#         samplerate=SAMPLE_RATE,
#         blocksize=BLOCKSIZE,
#         dtype="int16",
#         channels=1,
#         callback=callback,
#     ):
#         while True:
#             sd.sleep(1000)

# except KeyboardInterrupt:
#     print("\nStopped.")

from win import *
from enum import Enum
from pathlib import Path
import os


class AppMode(Enum):
    SOUND = 1
    CHAT = 2


class Config:
    api_url: str
    llm: str
    stt: str
    tts: str
    local_sound: bool
    default_mode: AppMode = AppMode.CHAT

    def __init__(self, **data):
        self.__dict__.update(data)


class App:
    Mode: AppMode = AppMode.CHAT

    def __init__(self):

        try:
            self.localData = Path(os.environ["HOME"]) / ".local" / "share" / "hamedi"
            with open(self.localData / "config.json", "r") as config_file:
                self.config = Config(**json.load(config_file))

        except Exception as e:
            print(f"Failed to load config file: {e}")
            sys.exit()

        Agent.LLM_MODEL = self.config.llm
        Agent.STT_MODEL = self.config.stt
        Agent.TTS_MODEL = self.config.tts
        self.Mode = AppMode(self.config.default_mode)
        print(f"App Mode: {self.Mode}")
        Agent.api_url = self.config.api_url
        self.app = QApplication(sys.argv)
        self.window = MainWindow()
        self.live=Voice.Live()
        self.speeker=None
        self.live.talk.connect(self.talk)
        
        match self.Mode:
            case AppMode.CHAT:
                self.window=MainWindow()
                self.window.show()
            case AppMode.SOUND:
                self.startSoundMode()
            case _:

                sys.exit(1)
        
        sys.exit(self.app.exec())
        
    def startSoundMode(self):
        self.live.start()
    def talk(self,text):
        print(f"User sayed: {text}")
        if self.is_talks_bot(text):
            Agent.send(text)
            self.say(Agent.res)
        pass
    def is_talks_bot(self,text)->bool:
        return True
    def say(self,text):
        if self.Mode==AppMode.SOUND:
            self.speeker=WorkerService(Agent.speek,text=text)
            self.speeker.start()


App()
