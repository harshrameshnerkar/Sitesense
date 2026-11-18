"""
Generates sample Inbound Delivery Notes in PDF format for SiteSense inspection testing.
Simulates real-world warehouse logistics paperwork.
"""

from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def create_delivery_note(filename: str, po_num: str, carrier: str, driver: str, pallets: int, seal: str, notes: str):
    output_path = Path("data/delivery_notes") / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a")
    )
    bold_label = ParagraphStyle(
        "BoldLabel",
        parent=styles["Normal"],
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#1e293b"),
        fontName="Helvetica-Bold"
    )
    val_style = ParagraphStyle(
        "ValStyle",
        parent=styles["Normal"],
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#334155")
    )

    story = []
    story.append(Paragraph("INBOUND FREIGHT DELIVERY NOTE & MANIFEST", title_style))
    story.append(Paragraph("<b>Destination:</b> SiteSense Warehouse Site 7 — Chicago Hub (Gate 4)", val_style))
    story.append(Spacer(1, 15))

    header_data = [
        [Paragraph("Purchase Order (PO):", bold_label), Paragraph(po_num, val_style),
         Paragraph("Date Received:", bold_label), Paragraph("2026-11-18", val_style)],
        [Paragraph("Carrier / Hauler:", bold_label), Paragraph(carrier, val_style),
         Paragraph("Trailer Seal #:", bold_label), Paragraph(seal, val_style)],
        [Paragraph("Driver Name:", bold_label), Paragraph(driver, val_style),
         Paragraph("Declared Pallets:", bold_label), Paragraph(str(pallets), val_style)],
    ]
    t_header = Table(header_data, colWidths=[120, 160, 120, 140])
    t_header.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_header)
    story.append(Spacer(1, 15))

    # Items table
    items_data = [
        ["Line", "Item SKU", "Description", "Pallet Qty", "Unit Weight (kg)", "Condition"],
        ["1", "SKU-IND-4091", "Safety Helmets (Type I, ANSI Z89.1)", "4", "320", "Intact / Verified"],
        ["2", "SKU-HAZ-2018", "Spill Berm Bunds & Absorbent Rolls", "2", "180", "Intact / Verified"],
        ["3", "SKU-EQP-8802", "Fire Extinguisher Mount Brackets", "3", "410", "Intact / Verified"],
        ["4", "SKU-PKG-1104", "Heavy Duty Pallet Stretch Film", str(max(1, pallets - 9)), "260", "Intact / Verified"],
    ]
    t_items = Table(items_data, colWidths=[35, 100, 220, 65, 80, 80])
    t_items.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e293b")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#94a3b8")),
        ('ALIGN', (3,1), (4,-1), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_items)
    story.append(Spacer(1, 15))

    notes_p = Paragraph(f"<b>Receiving Inspector Notes:</b> {notes}", val_style)
    story.append(notes_p)
    story.append(Spacer(1, 20))

    sig_data = [
        [Paragraph("Driver Signature: <i>J. Kowalski</i>", val_style),
         Paragraph("Receiving Clerk: <i>A. Johnson (Badge #441)</i>", val_style)]
    ]
    t_sig = Table(sig_data, colWidths=[270, 270])
    story.append(t_sig)

    doc.build(story)
    print(f"Generated Delivery Note: {output_path}")


def generate_all_delivery_notes():
    create_delivery_note(
        "delivery_note_po98421.pdf",
        po_num="PO-98421",
        carrier="Apex Logistics Express",
        driver="John Kowalski",
        pallets=14,
        seal="SEAL-88910",
        notes="High-confidence clean delivery. Seal verified before uncoupling. All pallets staged in Zone B."
    )
    create_delivery_note(
        "delivery_note_po98422.pdf",
        po_num="PO-98422",
        carrier="TransState Freight Line",
        driver="Carlos Mendez",
        pallets=10,
        seal="SEAL-44109",
        notes="Discrepancy noted: Carrier bill listed 12 skids; physical count is 10. Awaiting manager sign-off."
    )
    create_delivery_note(
        "delivery_note_po98423_scratched.pdf",
        po_num="PO-98423",
        carrier="Global Transit Direct",
        driver="Mark Peterson",
        pallets=6,
        seal="SEAL-11029",
        notes="Scanned copy faint. Low confidence OCR expected on line 3 quantity."
    )


if __name__ == "__main__":
    generate_all_delivery_notes()

