from docx import Document
import os

def generate_pdf(receiver, freq):
    document = Document("./static/base.docx")

    receiver = receiver.replace("būrys", "būriu").replace("pulkas", "pulku")

    for paragraph in document.paragraphs:
        for run in paragraph.runs:
            if "YYYYY" in run.text:
                run.text = run.text.replace("YYYYY", receiver)
                run.bold = True  # Make the replaced text bold
            if "yyyyy" in run.text:
                run.text = run.text.replace("yyyyy", receiver)
                run.bold = True  # Make the replaced text bold
            if "XXXX" in run.text:
                run.text = run.text.replace("XXXX", str(freq))

    modified_docx = "./static/document.docx"
    document.save(modified_docx)

    os.system("libreoffice --headless --convert-to pdf {} --outdir ./static".format(modified_docx))

