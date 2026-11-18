"""
Generates the official Warehouse Operations & Safety Policy Manual in both
Markdown and PDF format using ReportLab.
"""

from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak


POLICY_MD_CONTENT = """# ApexLogistics / SiteSense: Warehouse Operations & Compliance Manual
**Document Reference:** POL-SAF-2026-V4  
**Version:** v2026.Q4  
**Effective Date:** October 1, 2026  
**Scope:** Applicable across all physical distribution centers, retail storage rooms, and regional depots.

---

## Section 1: Pedestrian Walkways & Emergency Egress Clearances

### Clause 1.1: Walkway Delineation
All primary pedestrian pathways inside warehouse and depot facilities must be demarcated with high-visibility yellow or green boundary striping with a minimum clear width of 1.20 meters (48 inches).

### Clause 1.2: Egress Route Clearances
Emergency exit doors, primary egress aisles, and marked pedestrian routes must remain completely unobstructed at all times. Staging pallets, carton boxes, scrap material, or equipment in designated walkways is strictly prohibited. Any obstruction identified during inspection constitutes an immediate critical non-compliance finding.

### Clause 1.3: Dwell Time Limits
Materials, pallet jacks, or transport carts must not remain stationary within thoroughfare walkways for longer than three (3) consecutive minutes.

---

## Section 2: Fire Protection & Life Safety Equipment

### Clause 2.1: Fire Extinguisher Accessibility
All portable fire extinguishers must be mounted on designated columns or walls between 1.0 meter and 1.5 meters from floor level. An unobstructed hemispherical clearance radius of at least 1.00 meter (39 inches) must be preserved in front of and around each extinguisher unit at all times.

### Clause 2.2: Inspection Tagging & Maintenance
Every fire extinguisher must carry an active physical inspection tag signed and dated by a certified inspector within the preceding 12 calendar months. The pressure indicator needle must register firmly within the operational green zone.

### Clause 2.3: Life Safety Signage
Illuminated exit signage and high-visibility fire safety placards must be powered, fully legible, and mounted with line-of-sight visibility from all active working aisles.

---

## Section 3: Personal Protective Equipment (PPE) Protocols

### Clause 3.1: Mandatory Hard Hats (Safety Helmets)
ANSI Z89.1 certified safety helmets (Type I, Class E or G) are mandatory for all personnel, contractors, and visitors operating within high-bay storage racks, active forklift maneuvering zones, and freight intake bays.

### Clause 3.2: High-Visibility Apparel
High-visibility reflective vests or outerwear meeting EN ISO 20471 Class 2 or ANSI/ISEA 107 Class 2 standards must be worn continuously inside vehicle maneuvering and loading areas.

### Clause 3.3: Footwear Standards
All warehouse staff must wear protective steel-toe or composite-toe safety boots compliant with ASTM F2413 specifications.

---

## Section 4: Material Handling, Pallet Stacking & Racking

### Clause 4.1: Floor Stacking Height Limits
Free-standing wooden or composite pallets staged on warehouse floors must never exceed three (3) tiers in total height. Shrink-wrapped pallet loads must maintain vertical alignment without a lateral lean exceeding 5 degrees.

### Clause 4.2: Damaged Skid Quarantine
Pallets exhibiting cracked deck boards, broken stringers, protruding nails, or visible structural decay must be quarantined immediately and removed from active service.

### Clause 4.3: Racking Beam Load Verification
All structural pallet rack bays must display laminated manufacturer weight capacity labels on load beams. Beam deflection under load must not exceed 1/180th of the span length.

---

## Section 5: Chemical Safety & Spill Management

### Clause 5.1: Spill Containment Response
Any chemical, liquid oil, or hydraulic fluid release exceeding 0.5 liters must be cordoned off with warning hazard cones immediately. Absorbent pads or spill berms must be deployed within 15 minutes of occurrence.

### Clause 5.2: Safety Data Sheets (SDS) Availability
A current Safety Data Sheet (SDS) binder and eyewash emergency station must be situated within 25 meters walking distance of battery charging bays and chemical storage lockers.

---

## Section 6: Inbound Delivery & Manifest Verification

### Clause 6.1: Delivery Manifest Documentation
Every inbound shipment arriving at warehouse receiving docks must be accompanied by a physical or digital Delivery Note containing a valid Purchase Order (PO) number, carrier name, declared pallet count, and authorized driver signature.

### Clause 6.2: Security Seal Integrity
High-security bolt seals on freight trailers must be checked against the bill of lading before cutting. Broken or missing seals require supervisor notification and receiving hold.
"""


def generate_policy_files():
    policies_dir = Path("data/policies")
    policies_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Write Markdown file
    md_path = policies_dir / "warehouse_safety_policy.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(POLICY_MD_CONTENT)
    print(f"Written markdown policy: {md_path}")

    # 2. Generate PDF file using ReportLab
    pdf_path = policies_dir / "warehouse_safety_policy.pdf"
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1e3a8a"),
        spaceAfter=10
    )
    h2_style = ParagraphStyle(
        "SectionH2",
        parent=styles["Heading2"],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=12,
        spaceAfter=6
    )
    h3_style = ParagraphStyle(
        "ClauseH3",
        parent=styles["Heading3"],
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#334155"),
        spaceBefore=8,
        spaceAfter=4
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=6
    )
    meta_style = ParagraphStyle(
        "Meta",
        parent=styles["Italic"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=12
    )

    story = []
    
    # Header
    story.append(Paragraph("SiteSense / ApexLogistics: Warehouse Operations & Compliance Manual", title_style))
    story.append(Paragraph("<b>Document Ref:</b> POL-SAF-2026-V4 | <b>Effective:</b> Oct 1, 2026 | <b>Version:</b> v2026.Q4", meta_style))
    story.append(Spacer(1, 10))

    # Sections
    sections = [
        ("Section 1: Pedestrian Walkways & Emergency Egress Clearances", [
            ("Clause 1.1: Walkway Delineation", "All primary pedestrian pathways inside warehouse and depot facilities must be demarcated with high-visibility yellow or green boundary striping with a minimum clear width of 1.20 meters (48 inches)."),
            ("Clause 1.2: Egress Route Clearances", "Emergency exit doors, primary egress aisles, and marked pedestrian routes must remain completely unobstructed at all times. Staging pallets, carton boxes, scrap material, or equipment in designated walkways is strictly prohibited. Any obstruction identified during inspection constitutes an immediate critical non-compliance finding."),
            ("Clause 1.3: Dwell Time Limits", "Materials, pallet jacks, or transport carts must not remain stationary within thoroughfare walkways for longer than three (3) consecutive minutes.")
        ]),
        ("Section 2: Fire Protection & Life Safety Equipment", [
            ("Clause 2.1: Fire Extinguisher Accessibility", "All portable fire extinguishers must be mounted on designated columns or walls between 1.0 meter and 1.5 meters from floor level. An unobstructed hemispherical clearance radius of at least 1.00 meter (39 inches) must be preserved in front of and around each extinguisher unit at all times."),
            ("Clause 2.2: Inspection Tagging & Maintenance", "Every fire extinguisher must carry an active physical inspection tag signed and dated by a certified inspector within the preceding 12 calendar months. The pressure indicator needle must register firmly within the operational green zone."),
            ("Clause 2.3: Life Safety Signage", "Illuminated exit signage and high-visibility fire safety placards must be powered, fully legible, and mounted with line-of-sight visibility from all active working aisles.")
        ]),
        ("Section 3: Personal Protective Equipment (PPE) Protocols", [
            ("Clause 3.1: Mandatory Hard Hats (Safety Helmets)", "ANSI Z89.1 certified safety helmets (Type I, Class E or G) are mandatory for all personnel, contractors, and visitors operating within high-bay storage racks, active forklift maneuvering zones, and freight intake bays."),
            ("Clause 3.2: High-Visibility Apparel", "High-visibility reflective vests or outerwear meeting EN ISO 20471 Class 2 or ANSI/ISEA 107 Class 2 standards must be worn continuously inside vehicle maneuvering and loading areas."),
            ("Clause 3.3: Footwear Standards", "All warehouse staff must wear protective steel-toe or composite-toe safety boots compliant with ASTM F2413 specifications.")
        ]),
        ("Section 4: Material Handling, Pallet Stacking & Racking", [
            ("Clause 4.1: Floor Stacking Height Limits", "Free-standing wooden or composite pallets staged on warehouse floors must never exceed three (3) tiers in total height. Shrink-wrapped pallet loads must maintain vertical alignment without a lateral lean exceeding 5 degrees."),
            ("Clause 4.2: Damaged Skid Quarantine", "Pallets exhibiting cracked deck boards, broken stringers, protruding nails, or visible structural decay must be quarantined immediately and removed from active service."),
            ("Clause 4.3: Racking Beam Load Verification", "All structural pallet rack bays must display laminated manufacturer weight capacity labels on load beams. Beam deflection under load must not exceed 1/180th of the span length.")
        ]),
        ("Section 5: Chemical Safety & Spill Management", [
            ("Clause 5.1: Spill Containment Response", "Any chemical, liquid oil, or hydraulic fluid release exceeding 0.5 liters must be cordoned off with warning hazard cones immediately. Absorbent pads or spill berms must be deployed within 15 minutes of occurrence."),
            ("Clause 5.2: Safety Data Sheets (SDS) Availability", "A current Safety Data Sheet (SDS) binder and eyewash emergency station must be situated within 25 meters walking distance of battery charging bays and chemical storage lockers.")
        ]),
        ("Section 6: Inbound Delivery & Manifest Verification", [
            ("Clause 6.1: Delivery Manifest Documentation", "Every inbound shipment arriving at warehouse receiving docks must be accompanied by a physical or digital Delivery Note containing a valid Purchase Order (PO) number, carrier name, declared pallet count, and authorized driver signature."),
            ("Clause 6.2: Security Seal Integrity", "High-security bolt seals on freight trailers must be checked against the bill of lading before cutting. Broken or missing seals require supervisor notification and receiving hold.")
        ])
    ]

    for sec_title, clauses in sections:
        story.append(Paragraph(sec_title, h2_style))
        for c_title, c_text in clauses:
            story.append(Paragraph(c_title, h3_style))
            story.append(Paragraph(c_text, body_style))
        story.append(Spacer(1, 6))

    doc.build(story)
    print(f"Generated PDF policy manual: {pdf_path}")


if __name__ == "__main__":
    generate_policy_files()

