import os
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

    ShowTextToScreen(f"{Username}: {Query}")
    SetAssistantStatus("Thinking...")

    Decision = FirstLayerDMM(Query)

    G = any(i.startswith("general") for i in Decision)
    R = any(i.startswith("realtime") for i in Decision)

    merged_query = " and ".join(
        [" ".join(i.split()[1:]) for i in Decision if i.startswith(("general", "realtime"))]
    )

    for q in Decision:
        if any(q.startswith(f) for f in Functions):
            run(Automation(list(Decision)))
            return

    if R:
        SetAssistantStatus("Searching...")
        Answer = RealtimeSearchEngine(QueryModifier(merged_query))
    else:
        QueryFinal = Decision[0].replace("general ", "")
        Answer = ChatBot(QueryModifier(QueryFinal))

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
