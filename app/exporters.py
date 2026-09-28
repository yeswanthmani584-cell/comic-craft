import time
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_PDF_DIR = BASE_DIR / "static" / "comics"
STATIC_PANELS_DIR = BASE_DIR / "static" / "panels"
STATIC_PDF_DIR.mkdir(parents=True, exist_ok=True)

def save_pdf(layout: dict) -> str:
    timestamp = int(time.time())
    filename = f"comic_{timestamp}.pdf"
    pdf_path = STATIC_PDF_DIR / filename

    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    width, height = letter

    panels = layout.get("panels", [])
    story_texts = layout.get("story", [])

    for i, panel in enumerate(panels):
        c.setFillColorRGB(0.06, 0.09, 0.16)
        c.rect(0, 0, width, height, fill=1, stroke=0)

        c.setFillColorRGB(0.22, 0.74, 0.97)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(45, height - 40, f"COMICCRAFT AI - PANEL {i + 1}")

        raw_img_path = str(panel.get("image", ""))
        img_name = Path(raw_img_path).name
        target_img = STATIC_PANELS_DIR / img_name
        if not target_img.exists():
            target_img = BASE_DIR / raw_img_path.replace("\\", "/").lstrip("/")

        if target_img.exists():
            try:
                c.drawImage(str(target_img), 45, height - 430, width=520, height=370, preserveAspectRatio=True)
            except Exception:
                pass

        caption = story_texts[i] if i < len(story_texts) else f"Scene {i+1} continues."
        if isinstance(caption, dict):
            caption = str(caption.get("caption", caption.get("text", "")))
        caption = str(caption).replace("Panel 1:", "").replace("Panel 2:", "").replace("Panel 3:", "").replace("Panel 4:", "").strip()

        c.setFillColorRGB(0.12, 0.16, 0.23)
        c.roundRect(45, 60, 520, 100, 6, fill=1, stroke=0)
        c.setFillColorRGB(0.22, 0.74, 0.97)
        c.rect(45, 60, 6, 100, fill=1, stroke=0)

        c.setFillColorRGB(0.95, 0.98, 1.0)
        c.setFont("Helvetica", 11)
        c.drawString(65, 125, caption[:85])
        if len(caption) > 85:
            c.drawString(65, 105, caption[85:170])
        if len(caption) > 170:
            c.drawString(65, 85, caption[170:255])

        c.setFillColorRGB(0.55, 0.65, 0.75)
        c.setFont("Helvetica", 9)
        c.drawString(45, 30, f"Page {i + 1} of {len(panels)}")

        c.showPage()

    c.save()
    return filename