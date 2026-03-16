import os
from pypdf import PdfReader
from docx import Document

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_knowledge_base(folder=None):
    if folder is None:
        folder = os.path.join(BASE_DIR, "knowledge")

    all_text = []

    if not os.path.exists(folder):
        print(f"⚠️  Folder '{folder}' not found. Creating it...")
        os.makedirs(folder, exist_ok=True)
        return ""

    files = os.listdir(folder)
    if not files:
        print(f"⚠️  No files found in '{folder}'.")
        return ""

    for filename in files:
        path = os.path.join(folder, filename)
        text = ""
        try:
            if filename.lower().endswith(".pdf"):
                reader = PdfReader(path)
                text = "\n".join(p.extract_text() for p in reader.pages if p.extract_text())
                print(f"✅ Loaded PDF: {filename}")
            elif filename.lower().endswith(".docx"):
                doc = Document(path)
                text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
                print(f"✅ Loaded DOCX: {filename}")
            elif filename.lower().endswith((".txt", ".md")):
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read()
                print(f"✅ Loaded TXT: {filename}")
            elif filename.lower().endswith((".xlsx", ".xls")):
                import openpyxl
                wb = openpyxl.load_workbook(path)
                rows = []
                for sheet in wb.sheetnames:
                    ws = wb[sheet]
                    rows.append(f"-- Sheet: {sheet} --")
                    for row in ws.iter_rows(values_only=True):
                        row_text = " | ".join(str(c) for c in row if c is not None)
                        if row_text.strip():
                            rows.append(row_text)
                text = "\n".join(rows)
                print(f"✅ Loaded Excel: {filename}")
            else:
                print(f"⏭️  Skipped: {filename}")
                continue

            if text.strip():
                all_text.append(f"=== FILE: {filename} ===\n{text.strip()}")
        except Exception as e:
            print(f"❌ Error reading {filename}: {e}")

    print(f"\n📚 Loaded {len(all_text)} file(s) into knowledge base.\n")
    return "\n\n".join(all_text)