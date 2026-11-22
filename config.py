import os
from datetime import datetime
import pytz

BOT_TOKEN = os.getenv("BOT_TOKEN_1", "") + os.getenv("BOT_TOKEN_2", "")
OPENROUTER_KEY = os.getenv("OR_KEY_1", "") + os.getenv("OR_KEY_2", "")

MSK = pytz.timezone("Europe/Moscow")
AI_MODEL = "google/gemma-2-9b-it:free"

def now_msk():
    return datetime.now(MSK)
