"""
PDF Parser for SiteSense Knowledge Service.
Extracts page-by-page text from policy manuals and documents while preserving
page numbers and structural section headers.
"""

import os
from typing import List, Dict, Any
from pypdf import PdfReader


def parse_policy_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Reads a PDF document and returns a list of pages with page numbers and text.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Policy PDF not found at {pdf_path}")

    reader = PdfReader(pdf_path)
    pages_data = []

    for idx, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages_data.append({
            "page": idx,
            "text": text.strip()
        })

    return pages_data

