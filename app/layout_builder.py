def build_comic_layout(images: list, story, outline) -> dict:
    story_list = []
    
    # Safe conversion: String aanaal split seiyyum, list aanaal direct-ah edukkum
    if isinstance(story, str):
        if "**Panel" in story:
            parts = [p.strip() for p in story.split("**Panel") if p.strip()]
            story_list = [f"Panel {p}" for p in parts]
        else:
            story_list = [line.strip() for line in story.split("\n") if line.strip()]
    elif isinstance(story, list):
        for s in story:
            if isinstance(s, dict):
                story_list.append(str(s.get("caption", s.get("text", ""))))
            elif isinstance(s, list):
                story_list.append(" ".join([str(x) for x in s]))
            else:
                story_list.append(str(s))
    elif isinstance(story, dict):
        story_list = [str(v) for v in story.values()]

    default_captions = [
        "The adventure begins under mysterious circumstances.",
        "An unexpected anomaly warps the surroundings.",
        "Danger arrives without warning, testing their resolve.",
        "A critical turning point leads toward resolution."
    ]

    while len(story_list) < len(images):
        idx = len(story_list)
        story_list.append(default_captions[idx % len(default_captions)])

    panels = []
    for i, img_path in enumerate(images):
        caption = story_list[i] if i < len(story_list) else default_captions[i % 4]
        caption = str(caption).replace("Panel 1:", "").replace("Panel 2:", "").replace("Panel 3:", "").replace("Panel 4:", "").strip()
        panels.append({
            "panel_id": i + 1,
            "image": str(img_path),
            "caption": caption
        })

    return {
        "title": "ComicCraft AI",
        "panels": panels,
        "story": story_list[:len(images)]
    }