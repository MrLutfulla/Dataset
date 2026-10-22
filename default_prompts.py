# Boshlang'ich default toifalar va matnlar (Google Speech Commands va ASR standartlari)

DEFAULT_CATEGORIES = [
    {
        "code": "robot_cmd",
        "title": "🤖 Robot Buyruqlari (uz_robot_cmd)",
        "description": "Google Speech Commands standarti: 1 soniyalik aniq va qisqa robot harakat buyruqlari."
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
    },
    {
        "code": "commands",
        "title": "🗣 Smart-Uy Qisqa Buyruqlari",
        "description": "Aqlli yordamchi va maishiy texnika uchun ovozli buyruqlar."
    }
]

DEFAULT_PROMPTS = {
    "robot_cmd": [
        "oldinga",
        "orqaga",
        "chapga",
        "o'ngga",
        "to'xta",
        "tezroq",
        "sekinroq",
        "boshla",
        "yoq",
        "o'chir"
    ],
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
    ],
    "commands": [
        "Chiroqni yoq.",
        "Musiqani to'xtat.",
        "Konditsionerni yigirma to'rt darajaga qo'y.",
        "Eshikni qulfla.",
        "Ertaga soat yettiga budilnik o'rnat.",
        "Ovozni balandroq qil.",
        "Keyingi qo'shiqqa o'tkaz.",
        "Xonadagi haroratni ko'rsat.",
        "Televizorni o'chir.",
        "Xavfsizlik tizimini ishga tushir."
    ]
}
