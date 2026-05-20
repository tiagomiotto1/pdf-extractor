from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import pdfplumber
import tempfile
import os

app = FastAPI()  # ← estava faltando isso

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

                tables_as_text = ""
                for i, table in enumerate(page.extract_tables()):
                    tables_as_text += f"\nTABELA_{page.page_number}_{i}:\n"
                    for row in table:
                        clean = [str(c).strip() if c else "" for c in row]
                        tables_as_text += ",".join(clean) + "\n"

                full_text += text + tables_as_text + "\n\n"
    finally:
        os.unlink(tmp_path)

    return JSONResponse({"pageContent": full_text.strip()})

@app.get("/health")
def health():
    return {"status": "ok"}