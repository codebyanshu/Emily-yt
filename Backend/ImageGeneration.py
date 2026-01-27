import asyncio
from random import randint
from PIL import Image
import requests
from dotenv import load_dotenv
import os
from time import sleep

# =========================
# PATH SETUP (CRITICAL FIX)
# =========================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Backend/
DATA_DIR = os.path.join(BASE_DIR, "Data")
FRONTEND_FILE = os.path.join(BASE_DIR, "..", "Frontend", "Files", "ImageGeneration.data")

os.makedirs(DATA_DIR, exist_ok=True)

# =========================
# ENV
# =========================

load_dotenv()
HF_API_KEY = os.getenv("HF_API_KEY")

# =========================
# OPEN GENERATED IMAGES
# =========================

def open_images(prompt):
    prompt = prompt.replace(" ", "_")

    for i in range(1, 5):
        image_path = os.path.join(DATA_DIR, f"{prompt}{i}.jpg")
        try:
            img = Image.open(image_path)
            print(f"Opening image: {image_path}")
            img.show()
            sleep(1)
        except IOError:
            print(f"Unable to open image: {image_path}")

# =========================
# HUGGINGFACE API
# =========================

API_URL = "https://api-inference.huggingface.co/models/stable-diffusion-xl-base-1.0"
headers = {"Authorization": f"Bearer {HF_API_KEY}"}

async def query(payload):
    response = await asyncio.to_thread(
        requests.post,
        API_URL,
        headers=headers,
        json=payload,
        timeout=120
    )
    return response.content

# =========================
# IMAGE GENERATION
# =========================

async def generate_image(prompt: str):
    tasks = []

    for _ in range(4):
        payload = {
            "inputs": f"{prompt}, sharpness maximum, ultra HD, 8k, highly detailed, photorealistic, seed={randint(1, 1000000)}",
            "options": {"wait_for_model": True}
        }
        tasks.append(asyncio.create_task(query(payload)))

    image_bytes_list = await asyncio.gather(*tasks)

    for i, image_bytes in enumerate(image_bytes_list):
        img_path = os.path.join(DATA_DIR, f"{prompt.replace(' ', '_')}{i+1}.jpg")
        with open(img_path, "wb") as f:
            f.write(image_bytes)

def GenerateImage(prompt: str):
    asyncio.run(generate_image(prompt))
    open_images(prompt)

# =========================
# FILE WATCHER LOOP
# =========================

while True:
    try:
        with open(FRONTEND_FILE, "r") as f:
            data = f.read().strip()

        if not data:
            sleep(1)
            continue

        Status, prompt = data.split(",", 1)

        if Status == "True":
            print("Generating Image...")
            GenerateImage(prompt)

            with open(FRONTEND_FILE, "w") as f:
                f.write("False,False")

            break

        sleep(1)

    except Exception as e:
        print("Error:", e)
        sleep(1)
