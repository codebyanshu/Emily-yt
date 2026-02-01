from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import dotenv_values
import os
import mtranslate as mt
import atexit
import signal
import sys
import time

env_vars = dotenv_values('.env')

InputLanguge = env_vars.get("InputLanguge", "en")

HtmlCode = '''<!DOCTYPE html>
<html lang="en">
<head>
    <title>Speech Recognition</title>
</head>
<body>
    <button id="start" onclick="startRecognition()">Start Recognition</button>
    <button id="end" onclick="stopRecognition()">Stop Recognition</button>
    <p id="output"></p>
    <script>
        const output = document.getElementById('output');
        let recognition;

        function startRecognition() {
            recognition = new webkitSpeechRecognition() || new SpeechRecognition();
            recognition.lang = '';
            recognition.continuous = true;

            recognition.onresult = function(event) {
                const transcript = event.results[event.results.length - 1][0].transcript;
                output.textContent += transcript;
            };

            recognition.onend = function() {
                recognition.start();
            };
            recognition.start();
        }

        function stopRecognition() {
            recognition.stop();
            output.innerHTML = "";
        }
    </script>
</body>
</html>'''

with open(r"Data\Voice.html","w") as f:
    f.write(HtmlCode)
    
current_dir = os.getcwd()

Link = f"{current_dir}/Data/Voice.html"

chrom_options = Options()

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
chrom_options.add_argument(f'user-agent={user_agent}')
chrom_options.add_argument("--use-fake-ui-for-media-stream")
chrom_options.add_argument("--use-fake-device-for-media-stream")
chrom_options.add_argument("--headless=new")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrom_options)

TempDirPath = rf"{current_dir}/Frontend/Files"

def SetAssistantStatus(status):
    with open(rf"{TempDirPath}/Status.data","w",encoding='utf-8') as file:
        file.write(status)
        
def QueryModifier(Query):
    new_query = Query.lower().strip()
    query_words = new_query.split()
    question_words = ["what's", "whats", "please", "tell", "me", "about", "when","where", "who", "how", "can you", "do you", "define", "explain","what's","where's","who's","how's"]
    
    if any(word + " " in new_query for word in question_words):
        if query_words[-1][-1] in ['?', '.', '!']:
            new_query = new_query[:-1] + "?"
            
        else:
            new_query += "?"
    else:
        if query_words[-1][-1] in ['?', '.', '!']:
            new_query = new_query[:-1] + "."
        else:
            new_query += "."
    return new_query.capitalize()

def UniversalTranslator(text):
    english_translation = mt.translate(text, "en", "auto")
    return english_translation.capitalize()

def SpeechRecognition(Query):
    # Load the speech page and start recognition if needed
    try:
        driver.get("file:///" + Link)
        # start recognition (button handler exists in the page)
        try:
            driver.find_element(by=By.ID, value="start").click()
        except Exception:
            try:
                driver.execute_script("startRecognition();")
            except Exception:
                pass
    except Exception:
        pass

    # Poll the output element until text appears
    poll_interval = 0.05
    max_wait = 20.0
    start = time.time()
    while time.time() - start < max_wait:
        try:
            Text = driver.find_element(by=By.ID, value="output").text
            if Text and Text.strip():
                # attempt to stop recognition quickly
                try:
                    driver.find_element(by=By.ID, value="end").click()
                except Exception:
                    try:
                        driver.execute_script("stopRecognition();")
                    except Exception:
                        pass

                if InputLanguge.lower() != "en" or "en" in InputLanguge.lower():
                    return QueryModifier(Text)
                else:
                    SetAssistantStatus("Translating...")
                    return QueryModifier(UniversalTranslator(Text))
        except Exception:
            pass
        time.sleep(poll_interval)
    return ""


def StopSpeechRecognition():
    """Stop the recognition on the page and quit the browser driver."""
    global driver
    try:
        # call the page's stop function if available
        try:
            driver.execute_script("if (typeof stopRecognition === 'function') { stopRecognition(); }")
        except Exception:
            pass
        # try to stop the recognition object if accessible
        try:
            driver.execute_script("if (typeof recognition !== 'undefined') { try { recognition.stop(); } catch(e){} }")
        except Exception:
            pass
    except Exception:
        pass
    try:
        driver.quit()
    except Exception:
        pass


# Ensure cleanup on normal exit
atexit.register(StopSpeechRecognition)

# Ensure cleanup on SIGINT/SIGTERM
def _signal_handler(sig, frame):
    StopSpeechRecognition()
    try:
        sys.exit(0)
    except SystemExit:
        pass

signal.signal(signal.SIGINT, _signal_handler)
try:
    signal.signal(signal.SIGTERM, _signal_handler)
except Exception:
    # SIGTERM may not be available on Windows in some contexts
    pass
        
if __name__ == "__main__":
    while True:
        Text = SpeechRecognition("")
        print(Text)
