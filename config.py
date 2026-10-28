import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
SESSION_BATCH_SIZE = int(os.getenv("SESSION_BATCH_SIZE", "20"))
DB_PATH = BASE_DIR / os.getenv("DB_PATH", "dataset.db")
AUDIOS_DIR = BASE_DIR / "audios"

# Administratorlar ro'yxati (.env faylidan olinadi)
raw_admins = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(x.strip()) for x in raw_admins.split(",") if x.strip().isdigit()]

# Audios papkasi mavjud bo'lishini ta'minlash
AUDIOS_DIR.mkdir(parents=True, exist_ok=True)
