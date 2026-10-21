# 🎙 O'zbek Tili Ovozli Dataset Yig'ish Telegram Boti

Sun'iy intellekt, ovozni matnga aylantirish (ASR / STT), til modellarini o'qitish hamda ovozdan jins, yosh va hissiyotlarni (Speech Emotion Recognition) aniqlash uchun to'liq avtomatlashtirilgan dataset yig'ish platformasi.

---

## 🌟 Asosiy Imkoniyatlar

1. **Ko'p Spikerli Tizim (Multi-Speaker):**
   - Bitta Telegram akkauntidan bir nechta inson (o'zi, do'sti, oila a'zolari) nomidan ovoz yozish;
   - Har bir spiker uchun: **Ism**, **Jinsi** (Erkak/Ayol), **Yoshi** saqlanadi.
2. **Ko'p To'plamli Tizim (Dynamic Collections):**
   - Ovoz yozish bosilganda to'plam tanlash;
   - Admin panel orqali xohlagancha yangi to'plam ochish va `.txt` / `.csv` formatda matnlar yuklash;
   - Boshlang'ich to'plamlar:
     - 📖 **Umumiy ASR (Kitobiy/Neytral)**
     - 😊 **Quvnoq / Xursand (Emotion)**
     - 😢 **Yig'lamsirab / Mahzun (Emotion)**
     - 😠 **G'azab / Asabiy (Emotion)**
     - 🗣 **Qisqa Buyruqlar (Voice Commands)**
3. **Avtomatik 16kHz Mono WAV Standarti:**
   - Har bir kelgan Telegram ovozli xabari avtomatik tarzda `ffmpeg` orqali xalqaro ASR standartidagi **16000Hz Mono WAV** formatiga o'tkaziladi.
4. **Sessiya va Sifat Nazorati:**
   - 5 talik to'plam to'liq o'qilmaguncha asosiy datasetga kiritilmaydi (chala yozuvlar bekor qilinadi).
5. **Ustoz & Admin Boshqaruv Markazi (`/admin`):**
   - **📊 Jonli Statistika:** Jami foydalanuvchilar, spikerlar, jins/yosh nisbati, audio soatlari;
   - **📦 ZIP Eksport:** Barcha datasetlarni bitta ZIP yoki alohida to'plam/spiker bo'yicha `metadata.csv` (UTF-8 BOM) va `metadata.jsonl` (HuggingFace standartida) bilan yuklab olish;
   - **👥 Foydalanuvchilar & Guruhlar:** Jins, yosh bo'yicha saralash, qidiruv va spiker bo'yicha alohida yuklash;
   - **➕ Yangi To'plam Yaratish va Matnlar Yuklash:** Yangi yo'nalishlar ochish.

---

## 🤖 Botdagi Buyruqlar

| Buyruq | Vazifasi | Kimlar uchun |
|---|---|---|
| `/start` | Botni ishga tushirish va asosiy menyu | Barcha |
| `/record` | Ovoz yozishni boshlash (to'plam tanlash) | Barcha |
| `/speakers` | Spikerlar ro'yxati (yangi shaxs qo'shish yoki almashtirish) | Barcha |
| `/collections` | Mavjud to'plamlar va matnlar ro'yxati | Barcha |
| `/mystats` | Foydalanuvchining shaxsiy hissa statistikasi | Barcha |
| `/help` | Botdan foydalanish bo'yicha to'liq yo'riqnoma | Barcha |
| `/admin` | Ustoz va administrator boshqaruv paneli | Faqat Adminlar |

---

## 🚀 O'rnatish va Ishga Tushirish

### 💻 1-usul: Windows Kompyuterda (1-klik orqali)

1. Ushbu papkadagi `.env.example` faylidan `.env` nusxasini oling (agar bo'lmasa avtomatik yaratiladi).
2. `.env` fayliga bot tokeningizni kiriting:
   ```env
   BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   SESSION_BATCH_SIZE=5
   DB_PATH=dataset.db
   ```
3. **`run.bat`** faylini ikki marta bosing!
   - U Python, kutubxonalar va FFmpeg mavjudligini avtomatik tekshiradi, yetishmayotganlarini o'rnatadi va botni ishga tushiradi.

---

### 🐧 2-usul: Linux VPS (Ubuntu / Debian) da

```bash
# 1. Tizim paketlarini o'rnatish
sudo apt update
sudo apt install -y python3 python3-pip python3-venv ffmpeg git

# 2. Virtual muhit yaratish
cd voice_dataset_bot
python3 -m venv .venv
source .venv/bin/activate

# 3. Kutubxonalarni o'rnatish
pip install -r requirements.txt

# 4. .env faylini sozlash
cp .env.example .env
nano .env

# 5. Ishga tushirish
python3 main.py
```

Doimiy fon rejimida (Systemd xizmati) ishlatish:
```ini
# /etc/systemd/system/voice_bot.service
[Unit]
Description=Voice Dataset Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/voice_dataset_bot
ExecStart=/root/voice_dataset_bot/.venv/bin/python3 main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now voice_bot
sudo systemctl status voice_bot
```

---

### 🐳 3-usul: Docker orqali

```bash
cd voice_dataset_bot
docker compose up -d --build
docker compose logs -f
```

---

## 📦 Dataset Tuzilishi va Eksport Formati

Admin paneldan yuklab olinadigan ZIP fayl quyidagi tuzilishga ega bo'ladi:

```
dataset_YYYYMMDD_HHMMSS.zip
├── audios/
│   ├── sess_3_p35_xxxx.wav
│   ├── sess_3_p36_xxxx.wav
│   └── ...
├── metadata.csv        # Excel va Python Pandas uchun (UTF-8 BOM)
└── metadata.jsonl      # HuggingFace Datasets va ASR modellari uchun
```

### `metadata.csv` ustunlari:
- `recording_id`: Ovoz yozuvining unikal ID si
- `audio_file`: Audio faylning nisbiy yo'li (`audios/sess_...wav`)
- `prompt_text`: O'qilgan asl matn
- `category_code`: Toifa kodi (`neutral`, `happy`, `sad`, `angry`, `commands`)
- `category_title`: Toifa nomi
- `speaker_name`: Spiker ismi
- `speaker_gender`: Jinsi (`male` / `female`)
- `speaker_age`: Yoshi
- `telegram_user_id`: Ovoz yuborgan Telegram foydalanuvchisi ID si
- `session_id`: 5 talik to'plam sessiyasi ID si
- `duration_seconds`: Audio davomiyligi (soniya)
- `file_size_bytes`: WAV fayl hajmi (bayt)
- `created_at`: Yozib olingan vaqt
