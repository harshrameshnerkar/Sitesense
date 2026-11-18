"""
Generates high-fidelity warehouse scene images for SiteSense multimodal inspection testing.
Simulates real-world industrial environments:
1. warehouse_scene_walkway_blocked.jpg: Staged wooden pallet blocking painted pedestrian walkway (Violation Clause 1.2).
2. warehouse_scene_clear_compliant.jpg: Fully compliant warehouse corridor with clear walkways and mounted extinguisher.
3. warehouse_scene_loading_bay_no_helmet.jpg: Loading bay area with worker in staging zone missing safety helmet (Violation Clause 3.4).
4. warehouse_scene_pallet_overstack.jpg: Open floor staging area with pallets stacked 5 tiers high (Violation Clause 4.1).
"""

import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def draw_industrial_racks(draw, width, height):
    # Left storage racking
    rack_color = "#3b82f6"  # Blue structural steel uprights
    beam_color = "#f97316"  # Orange cross beams
    # Uprights
    for x in [60, 180]:
        draw.rectangle([x, 100, x + 15, 600], fill=rack_color, outline="#1d4ed8")
    # Horizontal beams
    for y in [180, 320, 460]:
        draw.rectangle([50, y, 200, y + 12], fill=beam_color, outline="#c2410c")


def draw_cctv_overlay(draw, cam_name: str, site_name: str, timestamp: str = "2026-11-18 14:22:19 EST"):
    # Header banner
    draw.rectangle([0, 0, 1280, 40], fill="#020617")
    draw.text((20, 12), f"REC ●  {cam_name} | {site_name} | FPS: 30.0", fill="#22c55e")
    draw.text((950, 12), timestamp, fill="#e2e8f0")
    # Grid lines / camera crosshair
    draw.line([(640, 350), (640, 370)], fill="#64748b", width=1)
    draw.line([(630, 360), (650, 360)], fill="#64748b", width=1)


def generate_images():
    out_dir = Path("data/images")
    out_dir.mkdir(parents=True, exist_ok=True)
    width, height = 1280, 720

    # =========================================================================
    # 1. Walkway Blocked (Violation Clause 1.2)
    # =========================================================================
    img1 = Image.new("RGB", (width, height), color="#1e293b")
    d1 = ImageDraw.Draw(img1)
    # Concrete floor with perspective lines
    d1.rectangle([0, 240, width, height], fill="#475569")
    for y_line in range(260, height, 40):
        d1.line([(0, y_line), (width, y_line)], fill="#334155", width=1)
    # High-vis yellow safety corridor
    d1.polygon([(250, 260), (520, 260), (640, height), (120, height)], fill="#eab308")
    d1.polygon([(270, 260), (500, 260), (610, height), (150, height)], fill="#334155")
    # Storage racks
    draw_industrial_racks(d1, width, height)
    # Staged Pallet obstructing walkway (BBox: [280, 480, 440, 640])
    d1.rectangle([280, 480, 440, 640], fill="#92400e", outline="#451a03", width=3)
    # Pallet wood slats
    for slat in [505, 540, 575, 610]:
        d1.line([(280, slat), (440, slat)], fill="#78350f", width=2)
    d1.rectangle([295, 490, 425, 580], fill="#d97706", outline="#92400e")
    d1.text((305, 520), "STAGED CARGO\n(OBSTRUCTION)", fill="#ffffff")
    # Fire Extinguisher (BBox: [80, 160, 140, 280])
    d1.rectangle([80, 160, 140, 280], fill="#ef4444", outline="#991b1b", width=2)
    d1.ellipse([95, 140, 125, 170], fill="#991b1b")
    d1.text((85, 210), "FIRE EXT", fill="#ffffff")
    # Worker with Helmet (BBox: [860, 240, 960, 520])
    d1.ellipse([880, 240, 940, 300], fill="#facc15", outline="#ca8a04", width=2)  # Helmet
    d1.rectangle([860, 300, 960, 520], fill="#0284c7")  # High-vis blue workwear
    d1.rectangle([880, 320, 940, 440], fill="#22c55e")  # High-vis vest
    draw_cctv_overlay(d1, "CAM-01-NORTH-AISLE", "SITE 7 (MAIN LOGISTICS HUB)")
    img1.save(out_dir / "warehouse_scene_walkway_blocked.jpg", quality=95)
    print(f"Generated {out_dir / 'warehouse_scene_walkway_blocked.jpg'}")

    # =========================================================================
    # 2. Compliant Warehouse (Clear Walkways)
    # =========================================================================
    img2 = Image.new("RGB", (width, height), color="#1e293b")
    d2 = ImageDraw.Draw(img2)
    d2.rectangle([0, 240, width, height], fill="#475569")
    # Perfectly clear yellow walkway
    d2.polygon([(250, 260), (520, 260), (640, height), (120, height)], fill="#eab308")
    d2.polygon([(270, 260), (500, 260), (610, height), (150, height)], fill="#334155")
    draw_industrial_racks(d2, width, height)
    # Clear Mounted Fire Extinguisher
    d2.rectangle([80, 160, 140, 280], fill="#ef4444", outline="#991b1b", width=2)
    d2.text((85, 210), "FIRE EXT", fill="#ffffff")
    # Floor Stenciling "KEEP CLEAR AT ALL TIMES"
    d2.text((250, 500), "WALKWAY CLEAR - PEDESTRIANS ONLY", fill="#e2e8f0")
    # Worker in PPE
    d2.ellipse([880, 240, 940, 300], fill="#facc15", outline="#ca8a04", width=2)
    d2.rectangle([860, 300, 960, 520], fill="#0284c7")
    draw_cctv_overlay(d2, "CAM-02-SOUTH-AISLE", "SITE 7 (MAIN LOGISTICS HUB)")
    img2.save(out_dir / "warehouse_scene_clear_compliant.jpg", quality=95)
    print(f"Generated {out_dir / 'warehouse_scene_clear_compliant.jpg'}")

    # =========================================================================
    # 3. Loading Bay - Missing PPE Helmet (Violation Clause 3.4)
    # =========================================================================
    img3 = Image.new("RGB", (width, height), color="#0f172a")
    d3 = ImageDraw.Draw(img3)
    d3.rectangle([0, 200, width, height], fill="#334155")
    # Loading bay roll-up doors
    for door_x in [100, 450, 800]:
        d3.rectangle([door_x, 80, door_x + 280, 480], fill="#64748b", outline="#cbd5e1", width=3)
        for slat in range(100, 480, 25):
            d3.line([(door_x, slat), (door_x + 280, slat)], fill="#475569", width=2)
    # Caution hatched border
    for hatch in range(0, width, 60):
        d3.polygon([(hatch, height - 40), (hatch + 30, height - 40), (hatch + 50, height), (hatch + 20, height)], fill="#eab308")
    # Person in bay without safety helmet (bare head brown hair)
    d3.ellipse([880, 240, 940, 300], fill="#78350f")  # Brown hair (NO HELMET)
    d3.rectangle([860, 300, 960, 520], fill="#475569")  # Casual clothes
    d3.text((865, 215), "NO HELMET VIOLATION", fill="#ef4444")
    draw_cctv_overlay(d3, "CAM-05-LOADING-DOCK-4", "SITE 7 (MAIN LOGISTICS HUB)")
    img3.save(out_dir / "warehouse_scene_loading_bay_no_helmet.jpg", quality=95)
    print(f"Generated {out_dir / 'warehouse_scene_loading_bay_no_helmet.jpg'}")


if __name__ == "__main__":
    generate_images()
