# import json

# import time as timelib
# import sounddevice as sd
# import json
# from vosk import Model, KaldiRecognizer
# from ai import send
# import numpy as np
# from c_input import Voice
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
from w import *
app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())