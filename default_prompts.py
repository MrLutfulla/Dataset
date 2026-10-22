# Boshlang'ich default toifalar va matnlar (Google Speech Commands va ASR standartlari)

ROBOT_20_COMMANDS = [
    {"text": "Oldinga yur", "class": "FORWARD", "desc": "Oldinga harakat"},
    {"text": "Orqaga yur", "class": "BACKWARD", "desc": "Orqaga harakat"},
    {"text": "Chapga buril", "class": "LEFT", "desc": "Chapga burilish"},
    {"text": "O'ngga buril", "class": "RIGHT", "desc": "O'ngga burilish"},
    {"text": "To'xta", "class": "STOP", "desc": "Harakatni to'xtatish"},
    {"text": "Davom et", "class": "RESUME", "desc": "Harakatni davom ettirish"},
    {"text": "Boshlash", "class": "START", "desc": "Vazifani boshlash"},
    {"text": "Tezroq yur", "class": "SPEED_UP", "desc": "Tezlikni oshirish"},
    {"text": "Sekinroq yur", "class": "SLOW_DOWN", "desc": "Tezlikni kamaytirish"},
    {"text": "Chapga burilma", "class": "NO_LEFT", "desc": "Chapga burilmaslik"},
    {"text": "O'ngga burilma", "class": "NO_RIGHT", "desc": "O'ngga burilmaslik"},
    {"text": "To'siqni aylanib o't", "class": "AVOID", "desc": "To'siqni chetlab o'tish"},
    {"text": "Orqaga qayt", "class": "RETURN", "desc": "Qaytish"},
    {"text": "Uyga qayt", "class": "GO_HOME", "desc": "Bazaga qaytish"},
    {"text": "Qo'lni ko'tar", "class": "ARM_UP", "desc": "Robot manipulyatorini ko'tarish"},
    {"text": "Qo'lni tushir", "class": "ARM_DOWN", "desc": "Manipulyatorni tushirish"},
    {"text": "Ushla", "class": "GRAB", "desc": "Buyumni ushlash"},
    {"text": "Qo'yib yubor", "class": "RELEASE", "desc": "Buyumni qo'yish"},
    {"text": "Holatingni ko'rsat", "class": "STATUS", "desc": "Robot holatini so'rash"},
    {"text": "Takrorla", "class": "REPEAT", "desc": "Oxirgi amalni takrorlash"}
]

DEFAULT_CATEGORIES = [
    {
        "code": "robot_cmd",
        "title": "🤖 Robot Buyruqlari (uz_robot_cmd - 20 ta)",
        "description": "Google Speech Commands standarti: 20 ta aniq robot harakat va boshqaruv buyruqlari."
    },
    {
        "code": "unknown_words",
        "title": "📦 _unknown_ (Begona so'zlar)",
        "description": "Robot adashmasligi uchun fon/begona so'zlar to'plami."
    },
    {
        "code": "background_noise",
        "title": "🎧 _background_ (Shovqin va Jimlik)",
        "description": "Atrof-muhit shovqini, xona jimligi (10-60 soniyalik yozuvlar)."
    },
    {
        "code": "neutral",
        "title": "📖 Umumiy ASR (Kitobiy/Neytral)",
        "description": "Ovozni matnga aylantirish (Speech-to-Text) uchun ravon, xolis va kitobiy jumlalar."
    },
    {
        "code": "happy",
        "title": "😊 Quvnoq / Xursand (Emotion)",
        "description": "Ko'tarinki, shod-xurram, quvnoq hissiyot bilan aytiladigan jumlalar."
    },
    {
        "code": "sad",
        "title": "😢 Yig'lamsirab / Mahzun (Emotion)",
        "description": "G'amgin, mahzun, yig'lamsirab aytiladigan hissiyotli jumlalar."
    },
    {
        "code": "angry",
        "title": "😠 G'azab / Asabiy (Emotion)",
        "description": "Jiddiy, asabiy, qat'iy va g'azab ohangida aytiladigan jumlalar."
    }
]

DEFAULT_PROMPTS = {
    "robot_cmd": [item["text"] for item in ROBOT_20_COMMANDS],
    "unknown_words": [
        "non",
        "kitob",
        "olma",
        "suv",
        "qalam",
        "daraxt",
        "havo",
        "uy",
        "stol",
        "daftar"
    ],
    "background_noise": [
        "sokin xona jimligi (15-30 soniya mikrofonni ushlab turing)",
        "ofis fon shovqini (15-30 soniya mikrofonni ushlab turing)",
        "ko'cha yoki transport shovqini (15-30 soniya mikrofonni ushlab turing)"
    ],
    "neutral": [
        "O'zbekiston Markaziy Osiyoning yuragida joylashgan go'zal mamlakatdir.",
        "Sun'iy intellekt texnologiyalari ta'lim sifatini oshirishga katta hissa qo'shmoqda.",
        "Ertalab toza havoda sayr qilish inson salomatligi uchun juda foydali.",
        "Zamonaviy dasturlash tillari har yili yangi imkoniyatlar bilan boyib bormoqda.",
        "Kutubxonalardagi nodir qo'lyozmalar raqamli formatga o'tkazilmoqda.",
        "Quyosh energiyasidan foydalanish ekologik barqarorlikni ta'minlaydi.",
        "Orol dengizi havzasida yashil o'rmonzorlar barpo etilmoqda.",
        "Yosh olimlar xalqaro ilmiy konferensiyalarda o'z ishlarini muvaffaqiyatli taqdim etmoqdalar.",
        "Axborot xavfsizligi har bir tashkilot uchun birinchi darajali vazifadir.",
        "Toshkent shahridagi yangi metro bekatlari zamonaviy uslubda bezatilgan."
    ],
    "happy": [
        "Voy qoyil, bugun imtihondan eng yuqori ballni oldim, ishongim kelmayapti!",
        "Urra, nihoyat orzu qilgan musobaqamizda g'olib bo'ldik!",
        "Qaranglar, qanday ajoyib kun, kayfiyatim a'lo darajada!",
        "Bugun mening tug'ilgan kunim, barcha do'stlarim yig'ilishdi!",
        "Yashasin, kutgan xushxabarimiz nihoyat yetib keldi!",
        "Bu dunyodagi eng mazali taom bo'libdi, qo'llaringiz dard ko'rmasin!",
        "Biz bu loyihani birgalikda muvaffaqiyatli yakunladik, barchaga rahmat!",
        "Ajoyib sovg'a uchun sizga chin qalbimdan minnatdorchilik bildiraman!"
    ],
    "sad": [
        "Afsus, shuncha harakatlarimiz zoye ketdi, hech narsa o'xshamadi.",
        "Yuragim shunday ezilyaptiki, hatto gapirishga ham holim qolmadi.",
        "U mendan hech qanday sababsiz uzoqlashib ketdi, bu juda og'ir.",
        "Bugun negadir butun olam qorong'u va ma'nosizdek tuyulyapti.",
        "Kechirasiz, ko'z yoshlarimni to'xtata olmayapman, xafa bo'lmang.",
        "Nega har doim shunaqa nohaqliklar bo'laveradi, tushunmayman.",
        "Eski xotiralar yana yodimga tushib, ko'nglim buzildi.",
        "Endi hech narsani ortga qaytarib bo'lmaydi, hammasi kech."
    ],
    "angry": [
        "Yetar bas, qachongacha bu bema'nilikka chidab turishim kerak?!",
        "Senga ming marta aytdim, bu ishga aralashma deb!",
        "Bunaqa mas'uliyatsizlikni umrimda birinchi marta ko'rishim, uyaling!",
        "Darhol bu yerdan yo'qol, ko'zimga ko'rinma!",
        "Vaqtimni bekorga o'g'irlaganing yetadi, sabrimning ham chegarasi bor!",
        "Nega va'da bergan ishingni o'z vaqtida bajarmading, javob ber!",
        "Menga o'rgatma, o'z ishingni bilsang bo'lmaydimi?!",
        "Bu qaroringiz butun loyihani barbod qildi, tushunyapsizmi?!"
    ]
}
