import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes, convert_from_path
from pypdf import PdfReader
import re

pdf_path = "/Users/imran/Downloads/sg_judgements/[2024] SGCA 15.pdf"

text_overall = ""

pdf = convert_from_path(pdf_path, fmt='jpeg', dpi=150)

for page_num, page in enumerate(pdf):
    # left, top, right, bottom
    # these coordinates work with SG court proceedings saved as PDFs
    # coordinates also correspond to the dpi used
    page = page.crop((0, 0, page.width, 1500))
    
    text = pytesseract.image_to_string(page, config="--psm 1 --oem 1")
    if not re.search('table of content', text, re.IGNORECASE):
        text_overall += text
        #print(f"Page {page_num} - {text}")

print(text_overall)