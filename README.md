# 🎙 O'zbek Tili Ovozli Dataset Yig'ish Telegram Boti

Sun'iy intellekt, ovozni matnga aylantirish (ASR / STT), robototexnika va nutq buyruqlarini aniqlash (**Google Speech Commands standarti**), hamda ovozdan jins, yosh va hissiyotlarni (Speech Emotion Recognition) aniqlash uchun to'liq avtomatlashtirilgan dataset platformasi.

---

## 🌟 Asosiy Imkoniyatlar

1. **Google Speech Commands Standarti (`uz_robot_cmd`):**
   - **Audio formati:** WAV, 16 kHz, 16-bit PCM, mono, uzunligi roppa-rosa **1.0 soniya** (16000 ta sample);
   - **Avtomatik markazlashtirish:** Buyruq audio markazida bo'ladi, oldi va ortida tabiiy jimlik (silence padding) qoldiriladi;
   - **Papka tuzilmasi:** Har bir buyruq uchun alohida papka (`oldinga/`, `orqaga/`, `chapga/`, `o'ngga/`, `to'xta/`, `_unknown_/`, `_background_/`);
   - **Fayl nomi:** `diktoriD_buyruq_takror.wav` (masalan: `spk001_oldinga_01.wav`);
   - **`speakers.csv`:** `speaker_id, jins, yosh_guruhi, hudud, qurilma, muhit`;
   - **`splits.csv`:** Har bir diktor faqat bitta guruhda bo'ladi (80% train, 10% val, 10% test);
   - **`validation_list.txt` va `testing_list.txt`:** TensorFlow / PyTorch rasmiy loaderlari uchun tayyor fayllar.

2. **Ko'p Spikerli Tizim (Multi-Speaker):**
   - Bitta Telegram akkauntidan bir nechta inson nomidan ovoz yozish;
   - Har bir spiker uchun: **Ism**, **Jinsi** (Erkak/Ayol), **Yoshi**, **Yosh guruhi**, **Hudud**, **Qurilma** va **Muhit** saqlanadi.

3. **Ko'p To'plamli Tizim (Dynamic Collections):**
   - 🤖 **Robot Buyruqlari (`uz_robot_cmd`):** `oldinga`, `orqaga`, `chapga`, `o'ngga`, `to'xta`, `tezroq`, `sekinroq`, `boshla`, `yoq`, `o'chir`;
   - 📦 **_unknown_ (Begona so'zlar):** `non`, `kitob`, `olma`, `suv`, `qalam`, `daraxt`...;
   - 🎧 **_background_ (Shovqin va Jimlik):** Xona sukunati, ofis, ko'cha shovqini (10-60 soniya);
   - 📖 **Umumiy ASR (Kitobiy/Neytral);**
   - 😊 **Quvnoq / Xursand (Emotion);**
   - 😢 **Yig'lamsirab / Mahzun (Emotion);**
   - 😠 **G'azab / Asabiy (Emotion);**
   - 🗣 **Smart-Uy Qisqa Buyruqlari.**

4. **Sessiya va Sifat Nazorati:**
   - 5 talik to'plam to'liq o'qilmaguncha asosiy datasetga kiritilmaydi (chala yozuvlar bekor qilinadi).

5. **Ustoz & Admin Boshqaruv Markazi (`/admin`):**
   - **🤖 uz_robot_cmd ZIP Eksport:** 1 soniyalik Google Speech Commands standartidagi to'liq arxivni bitta tugma bilan yuklab olish;
   - **📊 Jonli Statistika:** Jami foydalanuvchilar, spikerlar, jins/yosh nisbati, audio soatlari;
   - **📦 Umumiy Dataset ZIP Eksport:** `metadata.csv` (UTF-8 BOM) va `metadata.jsonl` (HuggingFace standarti) bilan yuklash;
   - **👥 Foydalanuvchilar & Guruhlar:** Jins, yosh bo'yicha saralash, qidiruv va spiker bo'yicha alohida yuklash;
   - **➕ Yangi To'plam Yaratish:** Yangi yo'nalishlar ochish.

---

## 📂 Google Speech Commands Tuzilmasi

Admin paneldan **"🤖 uz_robot_cmd (Google Speech Commands ZIP)"** tugmasi orqali yuklab olinadigan arxiv tuzilishi:

```
uz_robot_cmd/
├── oldinga/
│   ├── spk001_oldinga_01.wav
│   ├── spk001_oldinga_02.wav
│   └── spk002_oldinga_01.wav
├── orqaga/
│   ├── spk001_orqaga_01.wav
│   └── ...
├── chapga/
├── o'ngga/
├── to'xta/
├── tezroq/
├── sekinroq/
├── boshla/
├── yoq/
├── o'chir/
├── _unknown_/          # Begona so'zlar (non, kitob, olma...)
├── _background_/       # Shovqin va jimlik (10-60s)
├── speakers.csv        # Diktorlar metama'lumotlari
├── splits.csv          # 80/10/10 train/val/test taqsimoti
├── validation_list.txt # Rasmiy validation ro'yxati
├── testing_list.txt    # Rasmiy test ro'yxati
└── README.txt          # Yo'riqnoma
```

### `speakers.csv` namunasi:
```csv
speaker_id,jins,yosh_guruhi,hudud,qurilma,muhit
spk001,ayol,18-25,Toshkent,smartfon,xona
spk002,erkak,26-40,Samarqand,naushnik,ofis
```

### `splits.csv` namunasi:
```csv
audio_path,speaker_id,command,split
oldinga/spk001_oldinga_01.wav,spk001,oldinga,train
oldinga/spk002_oldinga_01.wav,spk002,oldinga,test
```

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

1. Papkadagi `.env` fayliga bot tokeningiz kiritilganligini tekshiring (`.env.example` namunasi mavjud).
2. **`run.bat`** faylini ikki marta bosing!
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
