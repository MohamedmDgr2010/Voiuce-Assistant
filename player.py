import sounddevice as sd
import soundfile as sf
class AudioPlayer:
        def __init__(self):
            self.stream = None

        def play(self, audio_data,sr):
            self.stream = sd.RawOutputStream(samplerate=sr, channels=1, dtype="int16")

            self.stream.start()
            self.stream.write(audio_data)

        def stop(self):
            if self.stream and self.stream.active:
                self.stream.abort()
                self.stream.close()
                self.stream = None
