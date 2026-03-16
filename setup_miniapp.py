"""
Run this ONCE to set up the Mini App button in your bot menu.
Usage: python setup_miniapp.py
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    TOKEN = input("Enter your BOT_TOKEN: ").strip()

MINIAPP_URL = input("Enter your Railway URL (e.g. https://uznpuu-production.up.railway.app): ").strip()

# Remove trailing slash
MINIAPP_URL = MINIAPP_URL.rstrip("/")

print(f"\n🔧 Setting up Mini App button...")
print(f"   URL: {MINIAPP_URL}")

# Set menu button
res = requests.post(
    f"https://api.telegram.org/bot{TOKEN}/setChatMenuButton",
    json={
        "menu_button": {
            "type": "web_app",
            "text": "🎓 OʻzMPU App",
            "web_app": {"url": MINIAPP_URL}
        }
    }
)
data = res.json()
if data.get("result"):
    print("✅ Menu button set successfully!")
else:
    print("❌ Failed:", data)

# Set bot commands
res2 = requests.post(
    f"https://api.telegram.org/bot{TOKEN}/setMyCommands",
    json={
        "commands": [
            {"command": "start", "description": "Botni ishga tushirish"},
            {"command": "help",  "description": "Yordam"},
        ]
    }
)
print("✅ Commands set!")
print("\n🎉 Done! Open your bot in Telegram — you'll see the 🎓 button!")
print("   If you don't see it, restart the Telegram app.")
