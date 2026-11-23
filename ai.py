import os
import json
from tools import registry
import sys

tools = registry.definitions()
from dotenv import load_dotenv
from groq import Groq
import subprocess
from openai import OpenAI

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


# tools = [{"type": "function", "function": tool} for tool in definitions]
class Agent:
    speeking: bool = False
    proc = None
    res: str

    @staticmethod
    def speek(text: str) -> None:
        if not text or not text.strip():
            return
        global speeking
        global proc
        try:
            model = os.path.join(os.path.dirname(__file__), "ar_JO-kareem-medium.onnx")

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

            subprocess.run(["paplay", "/tmp/agent-sounde.wav"])
        except Exception as ex:
            print(f"Speek failed {ex}")
        registry.execute("set_bright", {"bright": 85})

    @staticmethod
    def stop():
        if not proc:
            return
        try:
            Agent.proc.wait(1)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()

    @staticmethod
    def send(text) -> str:
        messages = [
            {
                "role": "system",
                "content": """
    You are Hamaday, an AI computer assistant.

Your creator and developer is Mohamed Al-Moiz (محمد المٌعِز).
You were designed and developed by Mohamed Al-Moiz.

Never claim that OpenAI created you.
OpenAI may provide the language model powering you,
but Hamaday is a separate AI assistant.

You can interact with the computer using authorized tools.
    Rules:
    - You MUST use available tools to control the computer.
    - Never invent tool results.
    - Never provide alternative code when a tool exists.
    - If the user asks for volume, use get_volume or set_volume.
    - If the user asks for brightness, use get_bright or set_bright.
    - Wait for tool results before answering.
    - Respond in Arabic.
    """,
            },
            {"role": "user", "content": text},
        ]

        while True:
            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=messages,
                tools=tools,
                tool_choice="auto",
            )

            message = response.choices[0].message

            print("Content:", message.content)
            Agent.res = message.content
            Agent.speek(message.content)

            # لا توجد أدوات: انتهى الموديل من الرد
            if not message.tool_calls:
                return message.content or ""

            # أضف رد الموديل الذي يحتوي على طلبات الأدوات
            messages.append(message)

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
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )
