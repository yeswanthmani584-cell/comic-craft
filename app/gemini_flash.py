import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if api_key:
    genai.configure(api_key=api_key)

def get_flash_model():
    candidate_models = [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-1.5-flash-latest",
        "gemini-1.5-flash",
        "gemini-pro"
    ]
    for name in candidate_models:
        try:
            return genai.GenerativeModel(name)
        except Exception:
            continue
    return genai.GenerativeModel("gemini-1.5-flash")

def generate_outline(user_prompt: str) -> list:
    """
    Generates a structured 5-panel comic outline using Gemini Flash.
    """
    prompt = f"""
You are a professional comic book storyboard artist.
Generate a strictly formatted JSON array containing exactly 5 panel descriptions based on this story idea:
"{user_prompt}"

Each JSON object must have these exact keys:
"panel": (integer from 1 to 5)
"title": (creative short title string)
"scene_description": (detailed description of scene action and setting)
"image_prompt": (visual prompt describing characters, background, lighting, and camera angle)

Respond ONLY with the raw JSON array. Do not use markdown backticks or explanations.
"""
    try:
        model = get_flash_model()
        response = model.generate_content(prompt)
        text = response.text.strip()
        print("\n=== RAW GEMINI FLASH RESPONSE ===\n", text)

        if text.startswith("```"):
            lines = text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        data = json.loads(text)
        if isinstance(data, list) and len(data) == 5:
            return data
        elif isinstance(data, dict) and "panels" in data:
            return data["panels"]
    except Exception as e:
        print(f"[!] Gemini Flash Error: {e}. Using tailored outline fallback.")

    return [
        {
            "panel": 1,
            "title": "The Awakening",
            "scene_description": f"The story begins. {user_prompt}",
            "image_prompt": f"Dramatic comic book style, introduction scene, {user_prompt}"
        },
        {
            "panel": 2,
            "title": "The Discovery",
            "scene_description": "A mysterious anomaly appears, shifting reality.",
            "image_prompt": f"Close-up intense comic panel, glowing artifact, dramatic lighting, {user_prompt}"
        },
        {
            "panel": 3,
            "title": "The Rising Threat",
            "scene_description": "Stakes escalate quickly as unforeseen dangers emerge.",
            "image_prompt": f"Dynamic action shot, vibrant colors, comic strip style, {user_prompt}"
        },
        {
            "panel": 4,
            "title": "The Turning Point",
            "scene_description": "The protagonist confronts the challenge head-on with courage.",
            "image_prompt": f"Cinematic perspective, comic book illustration, suspense, {user_prompt}"
        },
        {
            "panel": 5,
            "title": "A New Horizon",
            "scene_description": "The conflict settles, resolving into a memorable ending.",
            "image_prompt": f"Epic wide-angle comic conclusion, vibrant, heroic ending, {user_prompt}"
        }
    ]