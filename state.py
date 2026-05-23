# state.py — Shared variables to avoid circular imports
from typing import Optional
import time

knowledge_base = ""
clients = {}
bot_app = None  # Will store the telegram.ext.Application instance

# Rate limiting state
user_rate_limits = {}

def check_rate_limit(user_id: str, max_requests: int = 2, window_seconds: int = 120) -> tuple[bool, int]:
    """
    Checks if a user has exceeded the rate limit.
    Returns: (is_allowed: bool, wait_time_seconds: int)
    """
    now = time.time()
    history = user_rate_limits.get(user_id, [])
    
    # Remove timestamps older than the window
    history = [t for t in history if now - t < window_seconds]
    
    if len(history) >= max_requests:
        user_rate_limits[user_id] = history
        oldest_in_window = history[0]
        wait_time = int(window_seconds - (now - oldest_in_window))
        return False, wait_time
        
    history.append(now)
    user_rate_limits[user_id] = history
    return True, 0
