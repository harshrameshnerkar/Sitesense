"""
Generates clean, realistic, raw warehouse photographs without any artificial labels,
bounding boxes, or text annotations. These represent unlabelled field photographs
or CCTV snapshots that users upload to SiteSense.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter


def draw_floor_and_perspective(draw, width, height, horizon=240):
    # Industrial grey concrete floor with lighting gradient
    for y in range(horizon, height):
        ratio = (y - horizon) / (height - horizon)
        r = int(71 + ratio * 30)
        g = int(85 + ratio * 30)
        b = int(105 + ratio * 30)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Concrete expansion joints / seam lines
    for x_origin in [150, 450, 750, 1050]:
        draw.line([(x_origin, horizon), (int(x_origin * 1.4 - 200), height)], fill="#334155", width=2)
    for y_seam in [320, 450, 600]:
        draw.line([(0, y_seam), (width, y_seam)], fill="#334155", width=1)


def draw_warehouse_background_racks(draw, width, horizon=240):
    # Distant warehouse walls and industrial steel pallet racking
    draw.rectangle([0, 0, width, horizon], fill="#1e293b")  # Dark upper warehouse ceiling / wall
    
    # Overhead lighting fixtures
    for light_x in [200, 500, 800, 1100]:
        draw.rectangle([light_x, 30, light_x + 80, 42], fill="#f8fafc")
        # Soft light beam
        draw.polygon([(light_x, 42), (light_x + 80, 42), (light_x + 180, horizon), (light_x - 100, horizon)], fill="#334155")

    # Steel rack columns in background
    for x in range(50, width, 180):
        draw.rectangle([x, 60, x + 16, horizon + 20], fill="#1d4ed8")  # Blue steel columns
        for beam_y in [90, 150, 210]:
            draw.rectangle([x - 10, beam_y, x + 170, beam_y + 10], fill="#ea580c")  # Orange load beams
            # Background pallet silhouettes
            draw.rectangle([x + 10, beam_y - 35, x + 80, beam_y], fill="#78350f")
            draw.rectangle([x + 85, beam_y - 45, x + 155, beam_y], fill="#b45309")


def draw_realistic_pallet_with_cartons(draw, x1, y1, x2, y2, stack_tiers=2):
    # Wooden pallet base
    pallet_height = 28
    base_top = y2 - pallet_height
    # Bottom skid runner boards
    draw.rectangle([x1, base_top + 18, x2, y2], fill="#78350f")
    # Top deck boards
    draw.rectangle([x1, base_top, x2, base_top + 10], fill="#92400e")
    for block_x in [x1 + 10, (x1 + x2) // 2 - 10, x2 - 30]:
        draw.rectangle([block_x, base_top + 8, block_x + 20, base_top + 20], fill="#451a03")

    # Corrugated brown cardboard cartons stacked on top
    box_bottom = base_top
    tier_height = (base_top - y1) // stack_tiers
    for tier in range(stack_tiers):
        t_y2 = box_bottom - (tier * tier_height)
        t_y1 = t_y2 - tier_height + 4
        # Two boxes side by side
        mid_x = (x1 + x2) // 2
        draw.rectangle([x1 + 4, t_y1, mid_x - 3, t_y2], fill="#d97706", outline="#92400e", width=2)
        draw.rectangle([mid_x + 3, t_y1, x2 - 4, t_y2], fill="#b45309", outline="#78350f", width=2)
        # Packaging tape across boxes
        draw.line([(x1 + 4, (t_y1 + t_y2) // 2), (mid_x - 3, (t_y1 + t_y2) // 2)], fill="#ca8a04", width=3)
        draw.line([(mid_x + 3, (t_y1 + t_y2) // 2), (x2 - 4, (t_y1 + t_y2) // 2)], fill="#ca8a04", width=3)


def generate_raw_images():
    out_dir = Path("data/images")
    out_dir.mkdir(parents=True, exist_ok=True)
    width, height = 1280, 720

    # =========================================================================
    # Image 1: Raw Unlabelled Walkway Obstruction
    # (Shows pallet sitting squarely in yellow pedestrian aisle - NO TEXT LABELS)
    # =========================================================================
    img1 = Image.new("RGB", (width, height))
    d1 = ImageDraw.Draw(img1)
    draw_floor_and_perspective(d1, width, height)
    draw_warehouse_background_racks(d1, width)

    # Yellow painted pedestrian corridor on floor
    d1.polygon([(260, 240), (520, 240), (660, height), (130, height)], fill="#eab308")
    d1.polygon([(280, 240), (500, 240), (630, height), (160, height)], fill="#475569")

    # Left wall with mounted red fire extinguisher
    d1.rectangle([70, 140, 150, 360], fill="#334155")  # Concrete column
    d1.rectangle([90, 180, 130, 280], fill="#dc2626", outline="#991b1b", width=2)  # Cylinder
    d1.ellipse([100, 165, 120, 190], fill="#020617")  # Valve & gauge
    d1.line([(100, 185), (85, 230)], fill="#020617", width=4)  # Black hose

    # Right side: Worker standing near rack
    d1.ellipse([885, 230, 935, 280], fill="#eab308")  # Hard hat
    d1.rectangle([870, 280, 950, 480], fill="#0369a1")  # Blue workwear
    d1.rectangle([880, 295, 940, 400], fill="#84cc16")  # Hi-vis vest

    # RAW UNLABELLED STAGED PALLET directly in the yellow walkway
    draw_realistic_pallet_with_cartons(d1, 280, 460, 480, 640, stack_tiers=2)

    img1 = img1.filter(ImageFilter.SMOOTH_MORE)
    img1.save(out_dir / "warehouse_raw_walkway_pallet.jpg", quality=95)
    print(f"Generated raw image: {out_dir / 'warehouse_raw_walkway_pallet.jpg'}")

    # =========================================================================
    # Image 2: Raw Unlabelled Clean Compliant Warehouse
    # (Clear yellow walkways, mounted extinguisher, worker in PPE - NO TEXT)
    # =========================================================================
    img2 = Image.new("RGB", (width, height))
    d2 = ImageDraw.Draw(img2)
    draw_floor_and_perspective(d2, width, height)
    draw_warehouse_background_racks(d2, width)

    # Completely clear yellow pedestrian corridor
    d2.polygon([(260, 240), (520, 240), (660, height), (130, height)], fill="#eab308")
    d2.polygon([(280, 240), (500, 240), (630, height), (160, height)], fill="#475569")

    # Column with fire extinguisher
    d2.rectangle([70, 140, 150, 360], fill="#334155")
    d2.rectangle([90, 180, 130, 280], fill="#dc2626", outline="#991b1b", width=2)
    d2.ellipse([100, 165, 120, 190], fill="#020617")

    # Compliant worker walking in designated path
    d2.ellipse([430, 320, 465, 360], fill="#eab308")  # Yellow hard hat
    d2.rectangle([420, 360, 475, 490], fill="#1e3a8a")  # Workwear
    d2.rectangle([425, 370, 470, 430], fill="#84cc16")  # Green hi-vis vest

    img2 = img2.filter(ImageFilter.SMOOTH_MORE)
    img2.save(out_dir / "warehouse_raw_clean_walkway.jpg", quality=95)
    print(f"Generated raw image: {out_dir / 'warehouse_raw_clean_walkway.jpg'}")

    # =========================================================================
    # Image 3: Raw Unlabelled Loading Bay with Missing PPE
    # (Roll-up bay door, trailer bumper, dock leveler, worker without helmet)
    # =========================================================================
    img3 = Image.new("RGB", (width, height))
    d3 = ImageDraw.Draw(img3)
    # Dark loading dock enclosure
    d3.rectangle([0, 0, width, height], fill="#1e293b")
    d3.rectangle([0, 280, width, height], fill="#334155")  # Concrete dock apron

    # Bay roll-up overhead doors
    for dx in [120, 520, 920]:
        d3.rectangle([dx, 60, dx + 260, 460], fill="#475569", outline="#94a3b8", width=3)
        for s in range(80, 460, 20):
            d3.line([(dx, s), (dx + 260, s)], fill="#334155", width=2)

    # Dock leveler steel ramp
    d3.polygon([(540, 460), (760, 460), (790, 560), (510, 560)], fill="#64748b", outline="#cbd5e1", width=2)
    for diamond in range(530, 770, 30):
        d3.line([(diamond, 465), (diamond + 15, 555)], fill="#475569", width=1)

    # Worker standing near open bay door WITHOUT safety helmet (brown hair)
    d3.ellipse([820, 330, 860, 375], fill="#451a03")  # Bare head / brown hair (NO HELMET)
    d3.rectangle([805, 375, 875, 520], fill="#334155")  # Casual hoodie / dark denim

    img3 = img3.filter(ImageFilter.SMOOTH_MORE)
    img3.save(out_dir / "warehouse_raw_loading_dock_worker.jpg", quality=95)
    print(f"Generated raw image: {out_dir / 'warehouse_raw_loading_dock_worker.jpg'}")

    # =========================================================================
    # Image 4: Raw Unlabelled Pallet Overstack
    # (Pallet stacked 5 tiers high - exceeding the 3-tier policy limit)
    # =========================================================================
    img4 = Image.new("RGB", (width, height))
    d4 = ImageDraw.Draw(img4)
    draw_floor_and_perspective(d4, width, height)
    draw_warehouse_background_racks(d4, width)

    # Draw overstacked pallet (5 tiers high, tall stack)
    draw_realistic_pallet_with_cartons(d4, 480, 160, 720, 620, stack_tiers=5)

    img4 = img4.filter(ImageFilter.SMOOTH_MORE)
    img4.save(out_dir / "warehouse_raw_overstacked_pallets.jpg", quality=95)
    print(f"Generated raw image: {out_dir / 'warehouse_raw_overstacked_pallets.jpg'}")

    # =========================================================================
    # Image 5: Raw Unlabelled Blocked Emergency Exit Door
    # (Exit door with green sign, pallets stacked in front of door)
    # =========================================================================
    img5 = Image.new("RGB", (width, height))
    d5 = ImageDraw.Draw(img5)
    # Concrete wall
    d5.rectangle([0, 0, width, height], fill="#334155")
    d5.rectangle([0, 340, width, height], fill="#475569")  # Floor

    # Emergency exit double doors
    d5.rectangle([450, 120, 750, 520], fill="#64748b", outline="#cbd5e1", width=4)
    d5.line([(600, 120), (600, 520)], fill="#334155", width=3)  # Center split
    # Panic push bars
    d5.rectangle([470, 320, 580, 335], fill="#ef4444")
    d5.rectangle([620, 320, 730, 335], fill="#ef4444")
    # Illuminated EXIT sign above door
    d5.rectangle([550, 70, 650, 110], fill="#16a34a", outline="#86efac", width=2)

    # Obstructing pallets stacked directly against exit door threshold
    draw_realistic_pallet_with_cartons(d5, 480, 420, 680, 580, stack_tiers=2)

    img5 = img5.filter(ImageFilter.SMOOTH_MORE)
    img5.save(out_dir / "warehouse_raw_exit_door_blocked.jpg", quality=95)
    print(f"Generated raw image: {out_dir / 'warehouse_raw_exit_door_blocked.jpg'}")


if __name__ == "__main__":
    generate_raw_images()
