"""
Visual Evidence Annotator for SiteSense.
Draws bounding boxes, confidence labels, and polygon zones onto images using Pillow.
Saves annotated visual evidence for inspection audit reports.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont


# High-contrast color palette for compliance annotations
CLASS_COLORS = {
    "fire_extinguisher": "#dc2626",  # Red
    "pallet": "#ea580c",             # Orange / Amber
    "safety_helmet": "#16a34a",      # Green
    "person": "#2563eb",             # Blue
    "spill": "#9333ea",              # Purple
    "blocked_exit": "#e11d48",       # Crimson
}
DEFAULT_COLOR = "#0284c7"


def annotate_image(
    image_path: str,
    output_path: str,
    detections: List[Dict[str, Any]],
    zones: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    Renders visual evidence:
    - Draws polygon boundaries for zones
    - Draws bounding boxes and labels for all detected objects
    - Saves output to output_path and returns the path
    """
    img = Image.open(image_path).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)

    # 1. Draw Zones (semi-transparent polygons)
    if zones:
        for z in zones:
            coords = [tuple(p) for p in z.get("polygon", [])]
            if len(coords) >= 3:
                # Yellow tint for walkway, blue tint for loading bay
                fill_color = (250, 204, 21, 60) if "walkway" in z["id"] else (59, 130, 246, 50)
                outline_color = (234, 179, 8, 220) if "walkway" in z["id"] else (37, 99, 235, 220)
                draw.polygon(coords, fill=fill_color, outline=outline_color)
                # Zone label
                centroid_x = sum(p[0] for p in coords) // len(coords)
                centroid_y = sum(p[1] for p in coords) // len(coords)
                draw.text((centroid_x - 40, centroid_y), f"ZONE: {z.get('name', z['id'])}", fill=(255, 255, 255, 240))

    # 2. Draw Detections
    for det in detections:
        bbox = det["bbox"]
        class_name = det.get("class_name", "object")
        conf = det.get("confidence", 0.0)
        zone_label = det.get("zone")

        x1, y1, x2, y2 = bbox
        color = CLASS_COLORS.get(class_name, DEFAULT_COLOR)

        # Draw thick rectangle
        draw.rectangle([x1, y1, x2, y2], outline=color, width=4)

        # Draw Label Banner
        label_text = f"{class_name.upper()} {int(conf * 100)}%"
        if zone_label:
            label_text += f" [{zone_label}]"

        banner_y1 = max(0, y1 - 22)
        banner_y2 = y1
        draw.rectangle([x1, banner_y1, x1 + len(label_text) * 9 + 12, banner_y2], fill=color)
        draw.text((x1 + 4, banner_y1 + 3), label_text, fill="#ffffff")

    # Composite overlay onto original image
    annotated = Image.alpha_composite(img, overlay).convert("RGB")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    annotated.save(output_path, quality=92)
    return output_path

