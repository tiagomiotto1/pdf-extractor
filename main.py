from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import pdfplumber
import tempfile
import os

app = FastAPI()

def clean_table_row(row):
    cleaned = [str(c).strip().replace('\n', ' ') if c else "" for c in row]
    while cleaned and cleaned[0] == "":
        cleaned.pop(0)
    while cleaned and cleaned[-1] == "":
        cleaned.pop()
    return cleaned

def extract_tables_from_page(page):
    tables_text = ""
    tables = page.extract_tables()
    if not tables:
        tables = page.extract_tables(table_settings={
            "vertical_strategy": "text",
            "horizontal_strategy": "text",
            "snap_tolerance": 5,
            "join_tolerance": 5,
        })
    for i, table in enumerate(tables):
        if not table:
            continue
        rows_text = []
        for row in table:
            cleaned = clean_table_row(row)
            if any(c for c in cleaned):
                rows_text.append(",".join(cleaned))
        if rows_text:
            tables_text += f"\nTABELA_{page.page_number}_{i}:\n"
            tables_text += "\n".join(rows_text) + "\n"
    return tables_text

@app.post("/extract")
async def extract_pdf(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    full_text = ""
    try:
        with pdfplumber.open(tmp_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                tables_text = extract_tables_from_page(page)
                full_text += text + tables_text + "\n\n"
    finally:
        os.unlink(tmp_path)

    return JSONResponse({"pageContent": full_text.strip()})

@app.get("/health")
def health():
    return {"status": "ok"}