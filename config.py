import os
from datetime import datetime
import pytz

BOT_TOKEN = os.getenv("BOT_TOKEN_1", "") + os.getenv("BOT_TOKEN_2", "")
OPENROUTER_KEY = os.getenv("OR_KEY_1", "").strip() + os.getenv("OR_KEY_2", "").strip()

MSK = pytz.timezone("Europe/Moscow")
AI_MODEL = "openrouter/free"

def now_msk():
    return datetime.now(MSK)
