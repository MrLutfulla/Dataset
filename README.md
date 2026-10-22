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

3. **Robot Buyruqlari (uz_robot_cmd - 20 ta asosiy buyruq):**
| № | O‘zbekcha buyruq | Sinf nomi (Class) | Vazifasi | Papka |
|:---:|:---|:---:|:---|:---|
| 1 | Oldinga yur | FORWARD | Oldinga harakat | `forward/` |
| 2 | Orqaga yur | BACKWARD | Orqaga harakat | `backward/` |
| 3 | Chapga buril | LEFT | Chapga burilish | `left/` |
| 4 | O‘ngga buril | RIGHT | O‘ngga burilish | `right/` |
| 5 | To‘xta | STOP | Harakatni to‘xtatish | `stop/` |
| 6 | Davom et | RESUME | Harakatni davom ettirish | `resume/` |
| 7 | Boshlash | START | Vazifani boshlash | `start/` |
| 8 | Tezroq yur | SPEED_UP | Tezlikni oshirish | `speed_up/` |
| 9 | Sekinroq yur | SLOW_DOWN | Tezlikni kamaytirish | `slow_down/` |
| 10 | Chapga burilma | NO_LEFT | Chapga burilmaslik | `no_left/` |
| 11 | O‘ngga burilma | NO_RIGHT | O‘ngga burilmaslik | `no_right/` |
| 12 | To‘siqni aylanib o‘t | AVOID | To‘siqni chetlab o‘tish | `avoid/` |
| 13 | Orqaga qayt | RETURN | Qaytish | `return/` |
| 14 | Uyga qayt | GO_HOME | Bazaga qaytish | `go_home/` |
| 15 | Qo‘lni ko‘tar | ARM_UP | Robot manipulyatorini ko‘tarish | `arm_up/` |
| 16 | Qo‘lni tushir | ARM_DOWN | Manipulyatorni tushirish | `arm_down/` |
| 17 | Ushla | GRAB | Buyumni ushlash | `grab/` |
| 18 | Qo‘yib yubor | RELEASE | Buyumni qo‘yish | `release/` |
| 19 | Holatingni ko‘rsat | STATUS | Robot holatini so‘rash | `status/` |
| 20 | Takrorla | REPEAT | Oxirgi amalni takrorlash | `repeat/` |

Qo'shimcha toifalar:
- 📦 **_unknown_ (Begona so'zlar):** non, kitob, olma, suv, qalam, daraxt...;
- 🎧 **_background_ (Shovqin va Jimlik):** Xona sukunati, ofis, ko'cha shovqini (10-60 soniya);
- 📖 **Umumiy ASR (Kitobiy/Neytral);**
- 😊 **Hissiyotlar (Quvnoq, Yig'lamsirab, G'azabli).**

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
├── forward/            # Oldinga yur (FORWARD)
│   ├── spk001_forward_01.wav
│   ├── spk001_forward_02.wav
│   └── spk002_forward_01.wav
├── backward/           # Orqaga yur (BACKWARD)
├── left/               # Chapga buril (LEFT)
├── right/              # O'ngga buril (RIGHT)
├── stop/               # To'xta (STOP)
├── resume/             # Davom et (RESUME)
├── start/              # Boshlash (START)
├── speed_up/           # Tezroq yur (SPEED_UP)
├── slow_down/          # Sekinroq yur (SLOW_DOWN)
├── no_left/            # Chapga burilma (NO_LEFT)
├── no_right/           # O'ngga burilma (NO_RIGHT)
├── avoid/              # To'siqni aylanib o't (AVOID)
├── return/             # Orqaga qayt (RETURN)
├── go_home/            # Uyga qayt (GO_HOME)
├── arm_up/             # Qo'lni ko'tar (ARM_UP)
├── arm_down/           # Qo'lni tushir (ARM_DOWN)
├── grab/               # Ushla (GRAB)
├── release/            # Qo'yib yubor (RELEASE)
├── status/             # Holatingni ko'rsat (STATUS)
├── repeat/             # Takrorla (REPEAT)
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
