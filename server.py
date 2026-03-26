import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv

load_dotenv()

# ── Path setup ─────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PORT = 8080

print(f"BASE_DIR: {BASE_DIR}")
print(f"PORT: {PORT}")
print(f"GROQ_API_KEY: {'SET' if os.environ.get('GROQ_API_KEY') else 'MISSING'}")
print(f"BOT_TOKEN: {'SET' if os.environ.get('BOT_TOKEN') else 'MISSING'}")

# ── Load AI ────────────────────────────────────────────────────────────────────
from file_loader import load_knowledge_base
from ai_responder import setup_ai, get_answer, parse_qa_pairs
from logger import get_stats, get_logs
import ai_responder

knowledge_base = load_knowledge_base(os.path.join(BASE_DIR, "knowledge"))
clients = setup_ai()
ai_responder._cached_pairs = parse_qa_pairs(knowledge_base)
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
print("✅ AI ready!")

# ── Handler ────────────────────────────────────────────────────────────────────
class Handler(BaseHTTPRequestHandler):

    def log_message(self, *a): pass

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

        elif path == '/api/auth':
            try:
                data = json.loads(body)
                self.send_json({"ok": data.get('password') == ADMIN_PASSWORD})
            except:
                self.send_json({"ok": False})
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

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

# ── Start ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print(f"🚀 Starting server on 0.0.0.0:{PORT}")
    server = HTTPServer(('0.0.0.0', PORT), Handler)
    print(f"✅ Server live on port {PORT}")
    server.serve_forever()
