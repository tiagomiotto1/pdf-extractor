from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
import pdfplumber
import tempfile
import os

app = FastAPI()

@app.post("/extract")
async def extract_pdf(
    file: UploadFile = File(...),
    project_id: str = Form(...)
):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    chunks = []
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

                full_text = text + tables_as_text
                if full_text.strip():
                    chunks.append({
                        "page": page.page_number,
                        "content": full_text,
                        "project_id": project_id
                    })
    finally:
        os.unlink(tmp_path)

    return JSONResponse({"chunks": chunks})

@app.get("/health")
def health():
    return {"status": "ok"}