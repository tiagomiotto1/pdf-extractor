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
    
    # Só detecção padrão — sem fallback "text" que contamina tudo
    tables = page.extract_tables()
    
    # Pega as bounding boxes das tabelas para remover do texto corrido
    table_bboxes = [table.bbox for table in page.find_tables()] if tables else []

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
    
    return tables_text, table_bboxes

@app.post("/extract")
async def extract_pdf(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    full_text = ""
    try:
        with pdfplumber.open(tmp_path) as pdf:
            for page in pdf.pages:
                tables_text, table_bboxes = extract_tables_from_page(page)

                # Extrai texto excluindo as áreas de tabela (evita duplicar)
                if table_bboxes:
                    filtered_page = page
                    for bbox in table_bboxes:
                        filtered_page = filtered_page.filter(
                            lambda obj, b=bbox: not (
                                b[0] <= obj["x0"] <= b[2] and
                                b[1] <= obj["top"] <= b[3]
                            )
                        )
                    text = filtered_page.extract_text() or ""
                else:
                    text = page.extract_text() or ""

                full_text += text + tables_text + "\n\n"
    finally:
        os.unlink(tmp_path)

    return JSONResponse({"pageContent": full_text.strip()})

@app.get("/health")
def health():
    return {"status": "ok"}