import fitz  # PyMuPDF

def extract_pages(file_path: str) -> list[dict]:
    """Returns [{page_number, text, needs_ocr, image_bytes}]"""
    doc = fitz.open(file_path)
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text().strip()
        needs_ocr = len(text) < 20  # heuristic: near-empty text layer = likely scanned/image slide
        image_bytes = None
        if needs_ocr:
            pix = page.get_pixmap(dpi=200)
            image_bytes = pix.tobytes("png")
        pages.append({
            "page_number": i + 1,
            "text": text,
            "needs_ocr": needs_ocr,
            "image_bytes": image_bytes,
        })
    doc.close()
    return pages