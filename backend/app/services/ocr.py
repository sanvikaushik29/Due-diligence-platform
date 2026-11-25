
import io
import os
import platform
import pytesseract
from PIL import Image

if platform.system() == "Windows":
    _win_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(_win_path):
        pytesseract.pytesseract.tesseract_cmd = _win_path

def ocr_page(image_bytes: bytes) -> str:
    img = Image.open(io.BytesIO(image_bytes))
    return pytesseract.image_to_string(img)
