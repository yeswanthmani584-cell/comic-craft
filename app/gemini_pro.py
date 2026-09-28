import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if api_key:
    genai.configure(api_key=api_key)

def get_pro_model():
    candidate_models = [
        "gemini-2.5-pro",
        "gemini-2.0-flash",
        "gemini-1.5-pro-latest",
        "gemini-1.5-pro",
        "gemini-pro"
    ]
    for name in candidate_models:
        try:
            return genai.GenerativeModel(name)
        except Exception:
            continue
    return genai.GenerativeModel("gemini-1.5-pro")

def generate_story(outline: list) -> str:
    """
    Expands the 5 panels into narration and character dialogue using Gemini Pro.
    """
    outline_text = "\n".join([
        f"Panel {p.get('panel', i+1)}: {p.get('title', '')} - {p.get('scene_description', '')}"
        for i, p in enumerate(outline)
    ])

    prompt = f"""
You are an award-winning comic book writer.
Write comic-style narration and character dialogues for each of the following panels:

{outline_text}

Format Rules:
- Start every panel section with strictly: **Panel 1: [Title]**, **Panel 2: [Title]**, etc.
- Include **CAPTION:** for setting the ambient atmosphere.
- Include **NARRATION:** describing the characters' actions.
- Include character dialogue lines formatted like **CHARACTER_NAME:** "Dialogue here".
- Keep the writing energetic, sharp, and true to classic comic books.
"""
    try:
        model = get_pro_model()
        response = model.generate_content(prompt)
        text = response.text.strip()
        if "**Panel" in text:
            return text
    except Exception as e:
        print(f"[!] Gemini Pro Error: {e}. Using scripted fallback.")

    story_blocks = []
    dialogues = [
        ('**CAPTION:** Silence fills the air...\n**NARRATION:** The journey begins under mysterious circumstances.\n**HERO:** "Everything changes starting today!"'),
        ('**CAPTION:** TICK... TICK... TICK...\n**NARRATION:** A strange anomaly warps the surroundings.\n**HERO:** "What kind of power is this?!"'),
        ('**CAPTION:** CRACKLE!\n**NARRATION:** Danger arrives without warning, testing their resolve.\n**FRIEND:** "Watch out! It\'s spreading!"\n**HERO:** "Stand behind me!"'),
        ('**CAPTION:** MAXIMUM FOCUS.\n**NARRATION:** Against impossible odds, a critical decision must be made.\n**HERO:** "There\'s only one shot left. I won\'t miss!"'),
        ('**CAPTION:** THE TIMELINE SETTLES.\n**NARRATION:** The dust clears as dawn breaks across the horizon.\n**FRIEND:** "We actually made it through."\n**HERO:** "Together, we can face whatever comes next."')
    ]

    for p, script in zip(outline, dialogues):
        story_blocks.append(f"**Panel {p.get('panel')}: {p.get('title')}**\n{script}")

    return "\n\n".join(story_blocks)