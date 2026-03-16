import os
from pypdf import PdfReader
from docx import Document

def load_knowledge_base(folder="knowledge/"):
    """Reads all PDF, DOCX, and TXT files from the knowledge folder."""
    all_text = []

    if not os.path.exists(folder):
        print(f"⚠️  Folder '{folder}' not found. Creating it...")
        os.makedirs(folder)
        return ""

    files = os.listdir(folder)
    if not files:
        print(f"⚠️  No files found in '{folder}'. Add your university documents there.")
        return ""

    for filename in files:
        path = os.path.join(folder, filename)
        text = ""

        try:
            if filename.lower().endswith(".pdf"):
                reader = PdfReader(path)
                text = "\n".join(
                    page.extract_text() for page in reader.pages if page.extract_text()
                )
                print(f"✅ Loaded PDF: {filename}")

            elif filename.lower().endswith(".docx"):
                doc = Document(path)
                text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
                print(f"✅ Loaded DOCX: {filename}")

            elif filename.lower().endswith((".txt", ".md")):
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read()
                print(f"✅ Loaded TXT: {filename}")

            else:
                print(f"⏭️  Skipped (unsupported): {filename}")
                continue

            if text.strip():
                all_text.append(f"=== FILE: {filename} ===\n{text.strip()}")

        except Exception as e:
            print(f"❌ Error reading {filename}: {e}")

    print(f"\n📚 Loaded {len(all_text)} file(s) into knowledge base.\n")
    return "\n\n".join(all_text)
