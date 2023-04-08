import base64
from io import BytesIO
import os

from PyPDF2 import PdfReader, PdfWriter
from pdf2image.pdf2image import convert_from_bytes


def parse_pdf(pdf_path, page_num=0):
    pdf_reader = PdfReader(str(pdf_path))
    writer = PdfWriter()

    pdf_name = ".".join(os.path.basename(pdf_path).split(".")[:-1])
    save_path = f"tmp/{pdf_name}/{page_num}.pdf"
    if os.path.isfile(save_path):
        return base64.b64encode(open(save_path, "rb").read()).decode("utf-8")
    if not os.path.isdir(f"tmp/{pdf_name}"):
        os.makedirs(f"tmp/{pdf_name}")

    if 0 > page_num or page_num > len(pdf_reader.pages):
        raise ValueError("Page number out of range")
    page = pdf_reader.pages[page_num]
    writer.add_page(page)

    writer.write(save_path)
    return base64.b64encode(open(save_path, "rb").read()).decode("utf-8")


def pdf_page_image(pdf_reader, pdf_name, page_num=0):
    save_path = f"tmp/{pdf_name}/{page_num}.png"
    if os.path.isfile(save_path):
        return open(save_path, "rb").read()
    if not os.path.isdir(f"tmp/{pdf_name}"):
        os.makedirs(f"tmp/{pdf_name}")
    if 0 > page_num or page_num > len(pdf_reader.pages):
        raise ValueError("Page number out of range")
    page = pdf_reader.pages[page_num]

    dst_pdf = PdfWriter()
    dst_pdf.add_page(page)
    pdf_bytes = BytesIO()
    dst_pdf.write(pdf_bytes)
    pdf_bytes.seek(0)

    img = convert_from_bytes(pdf_bytes.getvalue())[0]
    # img.convert("png")
    img.save(save_path)
    return open(save_path, "rb").read()
