# 🎙 O'zbek Tili Ovozli Dataset Yig'ish Telegram Boti

Sun'iy intellekt, ovozni matnga aylantirish (ASR/STT), til modellarini o'qitish hamda ovozdan jins, yosh va hissiyotlarni (Emotion Recognition) aniqlash uchun to'liq avtomatlashtirilgan dataset platformasi.

---

## 🌟 Asosiy Imkoniyatlar

1. **Ko'p Spikerli Tizim (Multi-Speaker):**
   - Bitta Telegram akkauntidan bir nechta inson (o'zi, ukasi, ota-onasi) nomidan ovoz yozish;
   - Har bir spiker uchun: **Ism**, **Jinsi** (Erkak/Ayol), **Yoshi** saqlanadi.
2. **Ko'p To'plamli Tizim (Dynamic Collections):**
   - Ovoz yozish bosilganda to'plam tanlash;
   - Admin xohlagancha yangi to'plam ochib, matnlar yuklay oladi;
   - Boshlang'ich to'plamlar: *Kitobiy ASR, Quvnoq, Yig'lamsirab/Mahzun, G'azabli, Qisqa buyruqlar*.
3. **Avtomatik 16kHz Mono WAV Format:**
   - Kelgan har bir audio avtomatik ravishda `ffmpeg` orqali ASR/STT modellari uchun xalqaro standart bo'lgan 16kHz mono `.wav` formatiga o'tkaziladi.
4. **Sessiya va Sifat Nazorati:**
   - 5 talik to'plam to'liq o'qilmaguncha asosiy datasetga kiritilmaydi.
5. **Ustoz & Admin Boshqaruv Markazi (`/admin`):**
   - **📊 Jonli Statistika:** Jami userlar, spikerlar, jinslar/yoshlar nisbati, umumiy audio soatlari;
   - **📦 ZIP Eksport:** Barcha datasetlarni bitta ZIP yoki alohida to'plam/spiker bo'yicha `metadata.csv` (UTF-8 BOM) va `metadata.jsonl` bilan yuklab olish;
   - **👥 Foydalanuvchilar & Guruhlar:** Jins (Erkak/Ayol), yosh toifalari bo'yicha saralash, qidiruv va aynan bitta spiker datasetini alohida yuklash;
   - **➕ Yangi To'plam Yaratish:** Matnlar bilan yangi dataset yo'nalishi ochish.

---

## 🚀 Yangi Serverga O'rnatish va Ishga Tushirish

### 1-usul: Docker orqali (Eng qulay va tavsiya etiladi)

Serverda Docker va Docker Compose o'rnatilgan bo'lsa:
```bash
# Loyiha papkasiga kiring
cd voice_dataset_bot

# Ishga tushiring
docker compose up -d --build
```
Loglarni ko'rish:
```bash
docker compose logs -f
```

---

### 2-usul: Linux VPS (Ubuntu / Debian) da Systemd orqali

1. Tizim paketlari va FFmpeg ni o'rnating:
   ```bash
   sudo apt update
   sudo apt install -y python3 python3-pip python3-venv ffmpeg
   ```

2. Virtual muhit oching va kutubxonalarni o'rnating:
   ```bash
   cd voice_dataset_bot
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Botni doimiy fon rejimida (systemd xizmati) ishlatish:
   `/etc/systemd/system/voice_bot.service` faylini yarating:
   ```ini
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

4. Xizmatni yoqing va ishga tushiring:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable voice_bot
   sudo systemctl start voice_bot
   sudo systemctl status voice_bot
   ```

---

### 3-usul: Windows kompyuterda

1. `requirements.txt` kutubxonalarini o'rnating:
   ```cmd
   pip install -r requirements.txt
   ```
2. `run.bat` faylini ikki marta bosing.
