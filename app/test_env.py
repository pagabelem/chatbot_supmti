# test_env.py
import os
from dotenv import load_dotenv
from app.core.config import settings

load_dotenv()
print("=== DEPUIS OS.ENVIRON ===")
print(f"TELEGRAM_BOT_TOKEN: {os.getenv('TELEGRAM_BOT_TOKEN')}")

print("\n=== DEPUIS SETTINGS ===")
print(f"settings.TELEGRAM_BOT_TOKEN: {settings.TELEGRAM_BOT_TOKEN}")