@app.post("/extract")
async def extract_pdf(file: UploadFile = File(...)):
    # remove project_id daqui - metadata fica no n8n
    chunks = []
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
                    "pageContent": full_text,  # ← já no formato do n8n
                    "metadata": { "page": page.page_number }
                })
    
    return JSONResponse({"chunks": chunks})