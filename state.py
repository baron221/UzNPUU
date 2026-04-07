# state.py — Shared variables to avoid circular imports
from typing import Optional

knowledge_base = ""
clients = {}
bot_app = None  # Will store the telegram.ext.Application instance
