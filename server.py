import os, json
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv

load_dotenv()
print("🔑 ENV CHECK — GROQ_API_KEY:", "SET" if os.environ.get("GROQ_API_KEY") else "MISSING")
print("🔑 ENV CHECK — BOT_TOKEN:", "SET" if os.environ.get("BOT_TOKEN") else "MISSING")

# Always resolve paths relative to this file's location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

from file_loader import load_knowledge_base
from ai_responder import setup_ai, get_answer, parse_qa_pairs
from logger import get_stats, get_logs
import ai_responder

load_dotenv()
knowledge_base = load_knowledge_base(os.path.join(BASE_DIR, "knowledge/"))
clients = setup_ai()
ai_responder._cached_pairs = parse_qa_pairs(knowledge_base)

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def do_GET(self):
        if self.path in ['/', '/index.html']:
            self.serve_file(os.path.join(BASE_DIR, 'miniapp', 'index.html'), 'text/html')
        elif self.path == '/admin' or self.path == '/admin.html':
            self.serve_file(os.path.join(BASE_DIR, 'miniapp', 'admin.html'), 'text/html')
        elif self.path == '/api/stats':
            self.send_json(get_stats())
        elif self.path == '/api/logs':
            logs = get_logs()
            self.send_json({"logs": logs[-50:][::-1]})
        else:
            self.send_response(404); self.end_headers()

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        if self.path == '/ask':
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
        elif self.path == '/api/auth':
            try:
                data = json.loads(body)
                if data.get('password') == ADMIN_PASSWORD:
                    self.send_json({"ok": True})
                else:
                    self.send_json({"ok": False})
            except:
                self.send_json({"ok": False})
        else:
            self.send_response(404); self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def serve_file(self, path, ct):
        try:
            with open(path, 'rb') as f: content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', ct + '; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_response(404); self.end_headers()

    def send_json(self, data):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    print(f"🌐 Server starting on port {port}...")
    print(f"🔐 Admin: /admin")
    server = HTTPServer(('0.0.0.0', port), Handler)
    print(f"✅ Server live on port {port}")
    server.serve_forever()