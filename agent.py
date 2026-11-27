import os
import json
from tools import registry
import sys

tools = registry.definitions()
from dotenv import load_dotenv
from groq import Groq
import subprocess
from openai import OpenAI

from session import Session
import soundfile as sf

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise RuntimeError("GROQ_API_KEY is missing")

client = Groq(api_key=api_key)

models = client.models.list()

for model in models.data:
    print(model.id)


# # Read tool definitions
# with open("tool_def.json", "r", encoding="utf-8") as file:
#     definitions = json.load(file)

# with open("tool_def.json", encoding="utf-8") as f:
#     definitions = json.load(f)

from PySide6.QtCore import QThread, Signal


class WorkerService(QThread):
    finished = Signal(str)

    def __init__(self, func: callable, **args):
        super().__init__()
        self.func = func
        self.args = args

    def run(self):
        self.func(**self.args)
        self.finished.emit("")


from player import AudioPlayer


# tools = [{"type": "function", "function": tool} for tool in definitions]
class Agent:
    speeking: bool = False

    res: str
    api_key: str
    api_url: str
    STT_MODEL: str
    TTS_MODEL: str
    LLM_MODEL: str
    AudioPlay = AudioPlayer()

    @staticmethod
    def speek(text: str) -> None:

        if not text or not text.strip():
            return

        try:
            model = os.path.join(os.path.dirname(__file__), Agent.TTS_MODEL)

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "piper",
                    "-m",
                    model,
                    "-f",
                    "/tmp/agent-sounde.wav",
                ],
                input=text,
                text=True,
                capture_output=True,
            )

            if result.returncode != 0:
                print("Piper error:")
                print(result.stderr)
                return

            audio, sr = sf.read("/tmp/agent-sounde.wav", dtype="int16")
            Agent.AudioPlay.play(audio, sr)
        except Exception as ex:
            print(f"Speek failed {ex}")

    @staticmethod
    def send(text) -> str:

        Session.messages.append({"role": "user", "content": text})
        while True:
            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=Session.messages,
                tools=tools,
                tool_choice="auto",
            )

            message = response.choices[0].message

            print("Content:", message.content)
            Agent.res = message.content
            # Agent.speek(message.content)

            # لا توجد أدوات: انتهى الموديل من الرد
            if not message.tool_calls:
                return message.content or ""

            # أضف رد الموديل الذي يحتوي على طلبات الأدوات
            Session.messages.append(message)

            for call in message.tool_calls:
                name = call.function.name
                arguments = json.loads(call.function.arguments)

                print("Name:", name)
                print("Arguments:", arguments)

                try:
                    result = registry.execute(name, arguments)
                except Exception as e:
                    result = {"error": str(e)}

                # أرسل نتيجة تنفيذ الأداة إلى سجل المحادثة
                Session.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )
