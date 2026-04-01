import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PORT = 8080

print(f"GROQ_API_KEY: {'SET' if os.environ.get('GROQ_API_KEY') else 'MISSING'}")
print(f"BOT_TOKEN: {'SET' if os.environ.get('BOT_TOKEN') else 'MISSING'}")

from file_loader import load_knowledge_base
from ai_responder import setup_ai, get_answer, parse_qa_pairs
from logger import get_stats, get_logs
import ai_responder

# Global state
knowledge_base = load_knowledge_base(os.path.join(BASE_DIR, "knowledge"))
clients = setup_ai()
ai_responder._cached_pairs = parse_qa_pairs(knowledge_base)
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
print("✅ AI ready!")


def reload_knowledge():
    global knowledge_base
    knowledge_base = load_knowledge_base(os.path.join(BASE_DIR, "knowledge"))
    ai_responder._cached_pairs = parse_qa_pairs(knowledge_base)
    print(f"🔄 Knowledge reloaded: {len(ai_responder._cached_pairs)} pairs")


class Handler(BaseHTTPRequestHandler):

    def log_message(self, *a):
        pass

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ['/', '/index.html']:
            self.serve_file(os.path.join(BASE_DIR, 'miniapp', 'index.html'), 'text/html')
        elif path in ['/admin', '/admin.html']:
            self.serve_file(os.path.join(BASE_DIR, 'miniapp', 'admin.html'), 'text/html')
        elif path == '/api/stats':
            self.send_json(get_stats())
        elif path == '/api/logs':
            self.send_json({"logs": get_logs()[-50:][::-1]})
        elif path == '/api/files':
            self.handle_list_files()
        elif path == '/health':
            self.send_json({"status": "ok"})
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not found')

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        path = self.path.split("?")[0]

        if path == '/ask':
            self.handle_ask(body)
        elif path == '/api/auth':
            self.handle_auth(body)
        elif path == '/api/upload':
            self.handle_upload(length, body)
        elif path == '/api/delete':
            self.handle_delete(body)
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def handle_ask(self, body):
        try:
            data = json.loads(body)
            question = data.get('question', '').strip()
            if not question:
                self.send_json({"answer": "Savol bo'sh!"}); return
            answer, options, lang, category = get_answer(question, knowledge_base, clients)
            if options:
                answer = answer + "\n\n" + "\n".join(f"• {o}" for o in options)
            self.send_json({"answer": answer})
        except Exception as e:
            self.send_json({"answer": f"Xatolik: {str(e)}"})

    def handle_auth(self, body):
        try:
            data = json.loads(body)
            self.send_json({"ok": data.get('password') == ADMIN_PASSWORD})
        except:
            self.send_json({"ok": False})

    def handle_list_files(self):
        try:
            folder = os.path.join(BASE_DIR, 'knowledge')
            files = []
            for f in os.listdir(folder):
                fp = os.path.join(folder, f)
                if os.path.isfile(fp):
                    files.append({
                        "name": f,
                        "size": round(os.path.getsize(fp) / 1024, 1),
                        "ext": os.path.splitext(f)[1].lower()
                    })
            self.send_json({"files": files})
        except Exception as e:
            self.send_json({"files": [], "error": str(e)})

    def handle_upload(self, length, body):
        try:
            ct = self.headers.get('Content-Type', '')
            if 'boundary=' not in ct:
                self.send_json({"ok": False, "error": "Invalid content type"}); return

            boundary = ct.split('boundary=')[1].strip().encode()
            parts = body.split(b'--' + boundary)
            filename = None
            filedata = None

            for part in parts:
                if b'Content-Disposition' not in part:
                    continue
                if b'filename=' not in part:
                    continue
                header_end = part.find(b'\r\n\r\n')
                if header_end == -1:
                    continue
                header = part[:header_end].decode('utf-8', errors='ignore')
                data = part[header_end + 4:]
                if data.endswith(b'\r\n'):
                    data = data[:-2]
                for h in header.split('\r\n'):
                    if 'filename=' in h:
                        fn = h.split('filename=')[1].strip().strip('"')
                        filename = os.path.basename(fn)
                filedata = data

            if not filename or filedata is None:
                self.send_json({"ok": False, "error": "No file found in request"}); return

            allowed = ('.pdf', '.docx', '.txt', '.xlsx', '.md')
            if not filename.lower().endswith(allowed):
                self.send_json({"ok": False, "error": "File type not allowed"}); return

            save_path = os.path.join(BASE_DIR, 'knowledge', filename)
            with open(save_path, 'wb') as f:
                f.write(filedata)
            reload_knowledge()
            self.send_json({"ok": True, "filename": filename, "pairs": len(ai_responder._cached_pairs)})
        except Exception as e:
            self.send_json({"ok": False, "error": str(e)})

    def handle_delete(self, body):
        try:
            data = json.loads(body)
            filename = os.path.basename(data.get('filename', ''))
            if not filename:
                self.send_json({"ok": False, "error": "No filename"}); return
            fp = os.path.join(BASE_DIR, 'knowledge', filename)
            if os.path.exists(fp):
                os.remove(fp)
                reload_knowledge()
                self.send_json({"ok": True})
            else:
                self.send_json({"ok": False, "error": "File not found"})
        except Exception as e:
            self.send_json({"ok": False, "error": str(e)})

    def serve_file(self, path, ct):
        try:
            with open(path, 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', ct + '; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(f'File not found: {path}'.encode())

    def send_json(self, data):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)


if __name__ == '__main__':
    print(f"🚀 Starting server on port {PORT}")
    server = HTTPServer(('0.0.0.0', PORT), Handler)
    print(f"✅ Server live on port {PORT}")
    server.serve_forever()