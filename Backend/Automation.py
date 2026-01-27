from AppOpener import close, open as appopen
from webbrowser import open as webopen
from pywhatkit import search,playonyt
from dotenv import dotenv_values , load_dotenv
from bs4 import BeautifulSoup
from rich import print
from groq import Groq
import webbrowser
import subprocess
import requests
import keyboard
import asyncio
import os

load_dotenv()
env_vars = dotenv_values(".env")
GroqAPIKey = os.getenv("GroqAPIKey")

# print(GroqAPIKey)

classes = ["zCubwf", "hgKElc", "LTKOO SY7ric", "ZOLcW", "gsrt vk_bk FzvWSb YwPhnf", "pclqee", "tw-Data-text tw-text-small tw-ta", "IZ6rdc", "05uR6d LTKOO", "vlzY6d","webanswers-webanswers_table_webanswers-table", "dDoNo ikb48b gsrt", "sXLa0e", "LWkfKe", "VQF4g", "qv3Wpe", "kno-rdesc", "SPZz6b"]

useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


client = Groq(api_key=GroqAPIKey)

professional_responses = [
    "your satisfaction is my priority; feel free to reach out if there's anything else I can help you with.",
    "I'm at your service for any additional questions or support you may need-don't hesitate to ask."
]

messages = []

SystemChatBot = [{"role" : "system", "content" : f"Hello,I am{os.environ['Username']},You are content writer.You have to write content for me like letters,application,story,text,youtube descriptions,code ,essays,notes,songs,poems ,etc. Be professional and polite while writing content. Use formal tone."}]

def GoogleSearch(Topic):
    search(Topic)
    return True

# GoogleSearch("yt")

def Content(Topic):
    
    def OpenNotepad(File):
        default_text_editor = "notepad.exe"
        subprocess.Popen([default_text_editor, File])
        
    def ContentWriterAI(prompt):
        messages.append({"role": "user", "content": f"{prompt}"})
        
        completion = client.chat.completions.create(
            model = "llama-3.1-8b-instant",
            messages = SystemChatBot + messages,
            max_tokens = 2048,
            temperature = 0.7,
            top_p = 1,
            stream = True,
            stop=None
        )
        
        Answer = ""
        
        for chunk in completion:
            if chunk.choices[0].delta.content:
                Answer += chunk.choices[0].delta.content
        Answer = Answer.replace("</s>","")
        messages.append({"role": "assistant", "content": Answer})
        
        return Answer
    Topic: str = Topic.replace("Content ","")
    ContentByAI = ContentWriterAI(Topic)
    
    with open(rf"Data\{Topic.lower().replace(' ','')}.txt","w",encoding="utf-8") as file:
        file.write(ContentByAI)
        file.close()
        
    OpenNotepad(rf"Data\{Topic.lower().replace(' ','')}.txt")
    return True

# Content("write an application for sick leave")
def YoutubeSearch(Topic):
    Url4Search = f"https://www.youtube.com/results?search_query={Topic.replace(' ','+')}"
    webbrowser.open(Url4Search)
    return True

def YoutubePlay(query):
    playonyt(query)
    return True
# YoutubePlay("hare rama hare krishna")


def OpenApp(app, sess=requests.Session()):
    # 1️⃣ Try opening installed app
    try:
        appopen(app, match_closest=True, output=False, throw_error=True)
        return True
    except:
        pass  # app not installed → go web

    # 2️⃣ Google search (spell mistakes handled by Google)
    def search_google(query):
        url = f"https://www.google.com/search?q={query}"
        headers = {
            "User-Agent": useragent,
            "Accept-Language": "en-US,en;q=0.9"
        }
        r = sess.get(url, headers=headers, timeout=10)
        return r.text if r.status_code == 200 else None

    # 3️⃣ Extract first REAL website link
    def extract_first_link(html):
        soup = BeautifulSoup(html, "html.parser")

        for a in soup.select("a"):
            href = a.get("href")
            if href and href.startswith("/url?q="):
                clean = href.split("/url?q=")[1].split("&")[0]
                if clean.startswith("http"):
                    return clean
        return None

    html = search_google(app)

    if html:
        link = extract_first_link(html)
        if link:
            webopen(link)
            return True

    # 4️⃣ Absolute fallback (never fails)
    webopen(f"https://www.google.com/search?q={app}")
    return True

# OpenApp("instagram")
# OpenApp("facebook")
# OpenApp("github")

def CloseApp(app):
    if "chrome" in app:
        pass
    else:
        try:
            close(app,match_closest=True,output=True,throw_error=True)
            return True
        except:
            return False
        
# CloseApp("whatsapp")
        
def System(command):
    
    def mute():
        keyboard.press_and_release("volume mute")
        
    def unmute():
        keyboard.press_and_release("volume mute")
    def volume_up():
        keyboard.press_and_release("volume up")
    def volume_down():
        keyboard.press_and_release("volume down")
    def shutdown():
        os.system("shutdown /s /t 1")
    def restart():
        os.system("shutdown /r /t 1")
    def signout():
        os.system("shutdown /l")
    commands = {
        "mute": mute,
        "unmute": unmute,
        "volume up": volume_up,
        "volume down": volume_down,
        "shutdown": shutdown,
        "restart": restart,
        "signout": signout
    }
    if command in commands:
        commands[command]()
        return True
    else:
        return False
    
async def TranslateAndExecute(commands:list[str]):
    funcs = []

    for command in commands:
        if command.startswith("open "):
            if "open it" in command:
                pass
            if "open file" in command:
                pass
            else:
                fun = asyncio.to_thread(OpenApp,command.removeprefix("open "))
                funcs.append(fun)
        elif command.startswith("general "):
            pass
        elif command.startswith("realtime "):
            pass
        elif command.startswith("close "):
            fun = asyncio.to_thread(CloseApp,command.removeprefix("close "))
            funcs.append(fun)

        elif command.startswith("play "):
            fun = asyncio.to_thread(YoutubePlay,command.removeprefix("play "))
            funcs.append(fun)
            
        elif command.startswith("google search " or "search "):
            fun = asyncio.to_thread(GoogleSearch,command.removeprefix("google search " or "search "))
            funcs.append(fun)
            

        elif command.startswith("youtube search " or "search on youtube "):
            fun = asyncio.to_thread(YoutubeSearch,command.removeprefix("youtube search "or "search on youtube "))
            funcs.append(fun)

        elif command.startswith("system "):
            fun = asyncio.to_thread(System,command.removeprefix("system "))
            funcs.append(fun)
        
        elif command.startswith("write " or "code " or "make "):
            fun = asyncio.to_thread(Content,command.removeprefix("write " or "code " or "make "))
            funcs.append(fun)

        else:
            print(f"No Function found. For {command}")
    
    results = await asyncio.gather(*funcs)

    for result in results:
        if isinstance(result,str):
            yield result
        else:
            yield result
            
async def Automation(commands:list[str]):

    async for result in TranslateAndExecute(commands):
        pass
    return True


# if __name__ == "__main__":
    # asyncio.run(Automation(["open yt","open insta","open telegram","play hanuman chilsa","search rcb","write a poem"]))
            
