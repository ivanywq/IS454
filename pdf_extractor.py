import os

from docx import Document
from docx.shared import Inches
from pypdf import PdfReader

pdf_path = os.path.join(os.getcwd(), "old_invoice")
################################################################
listoffiles = os.listdir(pdf_path)


################################################################
for i in range(0, len(listoffiles)):
    reader = PdfReader(pdf_path + "/" + listoffiles[i])
    with open(os.path.join(pdf_path, listoffiles[i].replace(".pdf", ".txt")), "a") as f:
        for page in reader.pages:
            f.write(page.extract_text() + "\n")
################################################################
