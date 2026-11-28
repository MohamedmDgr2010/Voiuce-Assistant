# Voiuce-Assistant

## A VoiceAssistant using 3 AI models

- STT (convert sound to text)
- LLM (thinking)
- TTS (convert text to sound)

 ---

### Goals

- Make private AI Agent.
- Practice creating AI agents.
- Reducing reliance on closed-source. software

---

### Features

- Using local STT model.
- Using local TTS model.
- Free & OpenSource.
- Saves user **data in your device**
- Can not access **ROOT** user

<hr style="height: 4px; background-color: black; border: none;">

## مساعد صوتي يعتمد على 3 نماذج ذكاء اصطناعي

- تحويل الصوت إلى نص (STT)
- نموذج لغوي ضخم (LLM) - (للتفكير والمعالجة)
- تحويل النص إلى صوت (TTS)

---

### الأهداف

- إنشاء وكيل ذكاء اصطناعي خاص.
- التدرب على بناء وكلاء الذكاء الاصطناعي.
- تقليل الاعتماد على البرمجيات مغلقة المصدر.

---

### المميزات

- استخدام نموذج محلي لتحويل الصوت إلى نص (STT).
- استخدام نموذج محلي لتحويل النص إلى صوت (TTS).
- مجاني ومفتوح المصدر.
- يحفظ بياناتك في جهازك
- لا يصل إلى صلاحيات **الروت**

## Download  التنزيل

```sh
git clone https://github.com/Agent01x/Voiuce-Assistant.git agent
cd agent
```

## INSTALL Python Env   تثبيت بيئة بايثون

```sh
python -m venv .venv
pip install -r requirements.txt
mkdir models
wget https://alphacephei.com/vosk/models/vosk-model-ar-mgb2-0.4.zip
unzip vosk-model-ar-mgb2-0.4.zip
python -m piper.download_voices ar_JO-kareem-low # You can download high يمكنك تنزل جودة اعلى للصوت

```

### Windows

```sh
mkdir %LOCALAPPDATA%/hamedi/
.venv\Scripts\Activate.ps1
```

### LINUX

```sh
mkdir $HOME/.local/share/hamedai/
source .venv/bin/activate
```

## Run التشغيل

```sh
# You must add API key efore run to process you tasks! لازم تستخدم مفتاح API 
# This app made for linux but it can work in windows! |  هذا التطبيق مصنوع لنظام لينكس , ربما يعمل على ويندوز!
python main.py
```

Mohamed Al-Moiz
محمد المعز
