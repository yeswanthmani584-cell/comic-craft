import os
import time
import traceback
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from fastapi import APIRouter, Request, Form
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates

from app.gemini_flash import generate_outline
from app.gemini_pro import generate_story
from app.image_generator import generate_image
from app.layout_builder import build_comic_layout
from app.exporters import save_pdf

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_PDF_DIR = BASE_DIR / "static" / "comics"
STATIC_PDF_DIR.mkdir(parents=True, exist_ok=True)
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

def to_web_path(path_str: str) -> str:
    if not path_str:
        return ""
    clean = str(path_str).replace("\\", "/").lstrip("/")
    return f"/{clean}"

def extract_prompt_str(item, fallback_text: str) -> str:
    if isinstance(item, dict):
        return str(item.get("image_prompt", item.get("prompt", fallback_text)))
    elif isinstance(item, list):
        flat = [str(x) for x in item if not isinstance(x, (list, dict))]
        return " ".join(flat) if flat else fallback_text
    elif isinstance(item, str) and item.strip():
        return item.strip()
    return fallback_text

def generate_all_images_fast(prompts: list) -> list:
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(generate_image, prompts))
    return [to_web_path(img) for img in results]

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={})

@router.get("/download-pdf/{filename}")
async def download_pdf_file(filename: str):
    pdf_path = STATIC_PDF_DIR / filename
    if pdf_path.exists():
        return FileResponse(
            path=str(pdf_path),
            filename="ComicCraft_Story.pdf",
            media_type="application/pdf"
        )
    return HTMLResponse("<h3>PDF not found</h3>", status_code=404)

@router.post("/generate", response_class=HTMLResponse)
async def generate_comic(
    request: Request,
    prompt: str = Form(...),
    character_name: str = Form(...),
    setting: str = Form(...),
    tone: str = Form(...),
    style: str = Form(...)
):
    try:
        full_prompt = f"{prompt}\nCharacter: {character_name}. Setting: {setting}. Tone: {tone}. Style: {style}."

        try:
            raw_outline = await run_in_threadpool(generate_outline, full_prompt)
        except Exception:
            raw_outline = []

        default_prompts = [
            f"{character_name} entering {setting}",
            f"{character_name} facing unexpected danger",
            f"{character_name} fighting back with focus",
            f"{character_name} victorious and smiling"
        ]

        image_prompts = []
        if isinstance(raw_outline, list) and len(raw_outline) > 0:
            for idx, item in enumerate(raw_outline):
                image_prompts.append(extract_prompt_str(item, default_prompts[idx % len(default_prompts)]))
        else:
            image_prompts = list(default_prompts)

        image_prompts = (image_prompts + default_prompts)[:4]

        try:
            full_story = await run_in_threadpool(generate_story, raw_outline)
        except Exception:
            full_story = []

        # Fix: String split error thadukkum safe parser
        story_lines = []
        if isinstance(full_story, list):
            for s in full_story:
                if isinstance(s, dict):
                    story_lines.append(str(s.get("caption", s.get("text", ""))))
                elif isinstance(s, list):
                    story_lines.append(" ".join([str(x) for x in s]))
                else:
                    story_lines.append(str(s))
        elif isinstance(full_story, dict):
            story_lines = [str(v) for v in full_story.values()]
        elif isinstance(full_story, str):
            story_lines = [line.strip() for line in full_story.split("\n") if line.strip()]

        default_stories = [
            f"{character_name} begins the journey in {setting}.",
            f"An unexpected challenge tests {character_name}'s power.",
            "Tension reaches its peak in a critical showdown.",
            f"Victory is claimed, bringing light back to the world."
        ]

        safe_story = []
        for i in range(4):
            if i < len(story_lines) and len(story_lines[i]) > 5:
                safe_story.append(story_lines[i])
            else:
                safe_story.append(default_stories[i])

        images = await run_in_threadpool(generate_all_images_fast, image_prompts)

        safe_outline = [{"image_prompt": p} for p in image_prompts]
        layout = await run_in_threadpool(build_comic_layout, images, safe_story, safe_outline)
        pdf_file_name = await run_in_threadpool(save_pdf, layout)

        # Vertical 1-by-1 Layout
        panels_html = ""
        for idx, img in enumerate(images, 1):
            caption = safe_story[idx - 1].replace("Panel 1:", "").replace("Panel 2:", "").replace("Panel 3:", "").replace("Panel 4:", "").strip()

            panels_html += f"""
            <div style="background:#1e293b; border:2px solid #38bdf8; border-radius:12px; padding:18px; margin-bottom:28px; width:100%; box-shadow:0 4px 15px rgba(0,0,0,0.5); box-sizing:border-box;">
                <h3 style="color:#38bdf8; margin:0 0 12px 0; font-size:20px; font-weight:bold;">PANEL {idx}</h3>
                <img src="{img}" style="width:100%; max-height:480px; object-fit:cover; border-radius:8px; background:#020617; display:block;" alt="Panel {idx}">
                <div style="margin-top:14px; background:#0f172a; border-left:5px solid #38bdf8; padding:12px 16px; border-radius:6px;">
                    <p style="color:#e2e8f0; font-size:15px; line-height:1.5; margin:0;">
                        <strong style="color:#38bdf8;">Story:</strong> {caption}
                    </p>
                </div>
            </div>
            """

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ComicCraft AI - Vertical Comic</title>
</head>
<body style="font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color:#0f172a; color:#f8fafc; padding:30px 15px; margin:0;">
    <div style="max-width:680px; margin:auto;">
        <div style="display:flex; justify-content:space-between; align-items:center; background:#1e293b; padding:16px 20px; border-radius:12px; margin-bottom:28px; border:1px solid #334155;">
            <a href="/" style="background:#475569; color:white; padding:10px 16px; border-radius:8px; text-decoration:none; font-weight:600;">← New Comic</a>
            <h2 style="margin:0; font-size:20px; color:#38bdf8;">Generated Comic</h2>
            <div style="display:flex; gap:8px;">
                <a href="/download-pdf/{pdf_file_name}" style="background:#2563eb; color:white; padding:10px 18px; border-radius:8px; text-decoration:none; font-weight:bold;">📥 Download PDF</a>
                <button onclick="window.print()" style="background:#0284c7; color:white; border:none; padding:10px 14px; border-radius:8px; cursor:pointer; font-weight:bold;">🖨️ Print</button>
            </div>
        </div>
        <div style="display:flex; flex-direction:column; align-items:center;">
            {panels_html}
        </div>
    </div>
</body>
</html>"""

        return HTMLResponse(content=html_content, status_code=200)

    except Exception as e:
        traceback.print_exc()
        return HTMLResponse(content=f"<h2 style='color:red;'>Error: {e}</h2>", status_code=500)