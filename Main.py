import os
import re
import json
import threading
from time import sleep
from asyncio import run
from dotenv import load_dotenv, dotenv_values

from Frontend.GUI import (
    GraphicalUserInterface,
    SetAssistantStatus,
    ShowTextToScreen,
    SetMicrophoneStatus,
    AnswerModifier,
    QueryModifier,
    GetAssistantStatus,
    GetMicrophoneStatus
)

from Backend.Model import FirstLayerDMM
from Backend.RealtimeSearchEngine import RealtimeSearchEngine
from Backend.Automation import Automation
from Backend.SpeachToText import SpeechRecognition
from Backend.ChatBot import ChatBot
from Backend.TextToSpeech import TextToSpeech
from Backend.whatsapp2 import WhatsAppController, parse_prompt
from Backend.ImageGeneration import generate as GenerateImage
import sys

# ---------------- ENV ----------------
load_dotenv()
env_vars = dotenv_values(".env")

Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "Emily")

DefaultMessage = f"Hello {Username}! I am {Assistantname}. How may I help you today?"

Functions = [
    "open", "close", "play", "system", "content",
    "google", "youtube", "search", "find",
    "launch", "execute", "run"
]

# ---------------- PATHS ----------------
BASE_DIR = os.getcwd()
TEMP_DIR = os.path.join(BASE_DIR, "Frontend", "Files")
DATA_DIR = os.path.join(BASE_DIR, "Data")

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# ---------------- FILE HELPERS ----------------
def file_path(name):
    return os.path.join(TEMP_DIR, name)

def ensure_file(path, default=""):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(default)

# ---------------- CHAT LOG ----------------
def ShowDefaultChatIfNoChats():
    chatlog = os.path.join(DATA_DIR, "ChatLog.json")
    ensure_file(chatlog, "[]")

    with open(chatlog, "r", encoding="utf-8") as f:
        if len(f.read()) < 5:
            ensure_file(file_path("Database.data"))
            ensure_file(file_path("Response.data"), DefaultMessage)

def ReadChatLogJson():
    with open(os.path.join(DATA_DIR, "ChatLog.json"), "r", encoding="utf-8") as f:
        return json.load(f)

def ChatLogIntegration():
    data = ReadChatLogJson()
    formatted = ""

    for entry in data:
        if entry["role"] == "user":
            formatted += f"{Username}: {entry['content']}\n"
        elif entry["role"] == "assistant":
            formatted += f"{Assistantname}: {entry['content']}\n"

    with open(file_path("Database.data"), "w", encoding="utf-8") as f:
        f.write(AnswerModifier(formatted))

def ShowChatsOnGUI():
    ensure_file(file_path("Database.data"))
    ensure_file(file_path("Responses.data"))

    with open(file_path("Database.data"), "r", encoding="utf-8") as f:
        data = f.read()

    if data.strip():
        with open(file_path("Responses.data"), "w", encoding="utf-8") as f:
            f.write(data)

# ---------------- INIT ----------------
def InitialExecution():
    SetMicrophoneStatus("False")
    ShowTextToScreen("Initializing Assistant...")
    ShowDefaultChatIfNoChats()
    ChatLogIntegration()
    ShowChatsOnGUI()

InitialExecution()

# ---------------- MAIN LOGIC ----------------
def MainExecution():
    SetAssistantStatus("Listening...")
    Query = SpeechRecognition("")

    if not Query:
        return

    # Quick route: if the user asked something intended for WhatsApp, refine and handle it.
    qlow = Query.strip()
    if qlow:
        low = qlow.lower()
        if (low.startswith(("call ", "video call ", "send ", "message ", "text ", "msg "))
                or "whatsapp" in low):
            def refine_whatsapp_prompt(q: str) -> str:
                s = q.strip()
                s = re.sub(r"\bon whatsapp\b", "", s, flags=re.IGNORECASE)
                s = re.sub(r"\bvia whatsapp\b", "", s, flags=re.IGNORECASE)
                s = s.replace("whatsapp", "")
                return s.strip()

            refined = refine_whatsapp_prompt(qlow)
            ShowTextToScreen(f"{Username}: {qlow}")
            # build a friendly assistant message and announce it
            parsed = parse_prompt(refined)
            if parsed:
                act = parsed.get("action")
                pname = parsed.get("name") or ""
                msg = parsed.get("message") or ""
                if act == "call":
                    assistant_phrase = f"Calling {pname} on WhatsApp."
                elif act == "video":
                    assistant_phrase = f"Starting a video call with {pname} on WhatsApp."
                elif act == "message":
                    assistant_phrase = f"Sending message to {pname}: {msg}"
                elif act == "open":
                    assistant_phrase = f"Opening WhatsApp chat with {pname}."
                else:
                    assistant_phrase = f"Opening WhatsApp for {pname}."
            else:
                assistant_phrase = "Opening WhatsApp..."

            SetAssistantStatus("Opening WhatsApp...")
            ShowTextToScreen(f"{Assistantname}: {assistant_phrase}")
            try:
                result = WhatsAppController(refined)
            except Exception as e:
                result = {"success": False, "error": str(e)}

            # speak and display a short confirmation, not the raw result dict
            if result.get("success"):
                ShowTextToScreen(f"{Assistantname}: Done.")
                TextToSpeech(assistant_phrase)
            else:
                err = result.get("error")
                ShowTextToScreen(f"{Assistantname}: Failed to perform WhatsApp action. {err}")
                TextToSpeech("Failed to perform WhatsApp action.")

            SetAssistantStatus("Available...")
            return

    ShowTextToScreen(f"{Username}: {Query}")
    SetAssistantStatus("Thinking...")

    Decision = FirstLayerDMM(Query)

    # ----- handle exit -----
    if any(i.startswith("exit") for i in Decision):
        ShowTextToScreen("Shutting down...")
        SetAssistantStatus("Shutting down...")
        SetMicrophoneStatus("False")
        sleep(0.5)
        sys.exit(0)

    # ----- automation / system-like commands -----
    if any(any(d.startswith(f) for f in Functions) or d.startswith("system") for d in Decision):
        # Build a friendly phrase describing the requested automation
        parts = []
        for d in Decision:
            if d.startswith("open "):
                parts.append(d.replace("open ", "open "))
            elif d.startswith("close "):
                parts.append(d.replace("close ", "close "))
            elif d.startswith("play "):
                parts.append(d.replace("play ", "play "))
            elif d.startswith("system "):
                parts.append(d.replace("system ", "system command: "))
            elif d.startswith("write ") or d.startswith("content "):
                parts.append(d.replace("write ", "write ").replace("content ", "write content: "))
            else:
                parts.append(d)

        assistant_phrase = " and ".join(parts) if parts else "performing requested tasks"
        # Announce before execution
        ShowTextToScreen(f"{Assistantname}: {assistant_phrase}")
        TextToSpeech(assistant_phrase)

        SetAssistantStatus("Executing...")
        try:
            results = run(Automation(list(Decision)))
            SetAssistantStatus("Available...")

            # Build completion message
            success_count = sum(1 for r in results if r)
            if success_count == len(results):
                completion_phrase = "Done. I completed all requested tasks."
            elif success_count > 0:
                completion_phrase = f"Done. Completed {success_count} of {len(results)} tasks."
            else:
                completion_phrase = "I attempted the tasks but none completed successfully."

            ShowTextToScreen(f"{Assistantname}: {completion_phrase}")
            TextToSpeech(completion_phrase)
        except Exception as e:
            err = f"Automation error: {e}"
            ShowTextToScreen(f"{Assistantname}: {err}")
            TextToSpeech("There was an error executing the tasks.")
        return

    # ----- generate image -----
    gen_items = [d for d in Decision if d.startswith("generate") or "generate image" in d]
    if gen_items:
        for gi in gen_items:
            # extract prompt after keyword
            prompt = gi.split(None, 1)[1] if len(gi.split(None, 1)) > 1 else gi
            ShowTextToScreen(f"Generating image: {prompt}")
            SetAssistantStatus("Generating image...")
            try:
                ok = GenerateImage(prompt)
                if ok:
                    ShowTextToScreen("Image generation finished.")
                    TextToSpeech("Image generation completed.")
                else:
                    ShowTextToScreen("Image generation failed.")
                    TextToSpeech("Image generation failed.")
            except Exception as e:
                ShowTextToScreen(f"Image error: {e}")
                TextToSpeech("Image generation failed.")
        SetAssistantStatus("Available...")
        return

    # ----- realtime vs general -----
    G = any(i.startswith("general") for i in Decision)
    R = any(i.startswith("realtime") for i in Decision)

    merged_general = " and ".join([" ".join(i.split()[1:]) for i in Decision if i.startswith("general")])
    merged_realtime = " and ".join([" ".join(i.split()[1:]) for i in Decision if i.startswith("realtime")])

    if R:
        SetAssistantStatus("Searching...")
        Answer = RealtimeSearchEngine(QueryModifier(merged_realtime))
    elif G:
        SetAssistantStatus("Thinking...")
        Answer = ChatBot(QueryModifier(merged_general))
    else:
        # fallback: if Decision contains plain 'open/close/play' etc, delegate to Automation
        run(Automation(list(Decision)))
        return

    ShowTextToScreen(f"{Assistantname}: {Answer}")
    SetAssistantStatus("Answering...")
    TextToSpeech(Answer)

# ---------------- THREADS ----------------
def FirstThread():
    while True:
        if GetMicrophoneStatus() == "True":
            MainExecution()
        else:
            if GetAssistantStatus() != "Available...":
                SetAssistantStatus("Available...")
        sleep(0.1)

def SecondThread():
    GraphicalUserInterface()

# ---------------- RUN ----------------
if __name__ == "__main__":
    threading.Thread(target=FirstThread, daemon=True).start()
    SecondThread()
