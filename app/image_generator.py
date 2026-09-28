import os
import re
import time
import uuid
import random
import urllib.parse
import requests
from pathlib import Path
from PIL import Image, ImageDraw
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_PANELS_DIR = BASE_DIR / "static" / "panels"
STATIC_PANELS_DIR.mkdir(parents=True, exist_ok=True)

def sanitize_filename(prompt_text) -> str:
    clean = re.sub(r'[^a-zA-Z0-9_-]', '_', str(prompt_text)[:12])
    return f"{clean}_{uuid.uuid4().hex[:6]}.png"

def draw_canvas_panel(prompt_text, file_path: Path):
    width, height = 512, 512
    img = Image.new("RGB", (width, height), color=(15, 23, 42))
    draw = ImageDraw.Draw(img)
    draw.rectangle([8, 8, width - 8, height - 8], outline=(56, 189, 248), width=3)
    draw.text((30, 30), "SCENE READY", fill=(56, 189, 248))
    img.save(str(file_path), "PNG")

def generate_image(prompt, filename: str = None) -> str:
    # 1. Prompt extraction
    if isinstance(prompt, dict):
        raw_text = str(prompt.get("image_prompt", prompt.get("prompt", "")))
    elif isinstance(prompt, list):
        raw_text = " ".join([str(p) for p in prompt])
    else:
        raw_text = str(prompt)

    if not filename:
        filename = sanitize_filename(raw_text)

    file_path = STATIC_PANELS_DIR / filename

    # 2. Extract ONLY the visual action (Motha story paragraph-ai cut seigirom)
    # Remove long narrative clutter
    clean = re.sub(r'(The story begins|Scene:|A college student named|discovers a mysterious watch.*|The main character is.*|The setting is.*|The tone is.*|The art style is.*)', '', raw_text, flags=re.I)
    clean = re.sub(r'[^a-zA-Z0-9\s]', ' ', clean)
    clean = " ".join(clean.split()[:5]).strip()

    if not clean:
        clean = random.choice([
            "young man student mysterious room",
            "glowing watch device science room",
            "dramatic confrontation mystery shadow",
            "futuristic time rift glowing light",
            "hero standing triumphant sunrise"
        ])

    final_prompt = f"{clean}, comic book art, detailed illustration"
    encoded = urllib.parse.quote(final_prompt)
    seed = random.randint(1000, 999999)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    }

    # 3. Fast Dynamic URL
    endpoints = [
        f"https://image.pollinations.ai/prompt/{encoded}?width=512&height=512&seed={seed}&nologo=true",
        f"https://picsum.photos/seed/{seed}/512/512"
    ]

    for url in endpoints:
        try:
            res = requests.get(url, headers=headers, timeout=20)
            if res.status_code == 200 and len(res.content) > 3500:
                with open(file_path, "wb") as f:
                    f.write(res.content)
                print(f"[✓] Successfully downloaded: {filename}")
                return f"/static/panels/{filename}"
        except Exception as e:
            print(f"[!] Delay on endpoint, trying alternate: {e}")

    draw_canvas_panel(clean, file_path)
    return f"/static/panels/{filename}"