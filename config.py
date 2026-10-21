import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
SESSION_BATCH_SIZE = int(os.getenv("SESSION_BATCH_SIZE", "5"))
DB_PATH = BASE_DIR / os.getenv("DB_PATH", "dataset.db")
AUDIOS_DIR = BASE_DIR / "audios"

# Audios papkasi mavjud bo'lishini ta'minlash
AUDIOS_DIR.mkdir(parents=True, exist_ok=True)
