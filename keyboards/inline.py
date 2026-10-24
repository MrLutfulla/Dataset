from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_speakers_inline_keyboard(speakers: list, active_speaker_id: int = None) -> InlineKeyboardMarkup:
    buttons = []
    for sp in speakers:
        gender_icon = "👨" if sp["gender"] == "male" else "👩"
        is_active = (sp["id"] == active_speaker_id)
        mark = "✅ " if is_active else ""
        text = f"{mark}{gender_icon} {sp['name']}, {sp['age']} yosh"
        buttons.append([
            InlineKeyboardButton(text=text, callback_data=f"select_speaker:{sp['id']}")
        ])

    buttons.append([
        InlineKeyboardButton(text="➕ Yangi spiker qo'shish", callback_data="add_speaker")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_gender_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👨 Erkak", callback_data="set_gender:male"),
            InlineKeyboardButton(text="👩 Ayol", callback_data="set_gender:female")
        ],
        [
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")
        ]
    ])


def get_categories_inline_keyboard(categories: list, active_category_id: int = None) -> InlineKeyboardMarkup:
    buttons = []
    for cat in categories:
        is_active = (cat["id"] == active_category_id)
        mark = "✅ " if is_active else ""
        text = f"{mark}{cat['title']}"
        buttons.append([
            InlineKeyboardButton(text=text, callback_data=f"select_category:{cat['id']}")
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Jonli Statistika", callback_data="admin_stats"),
            InlineKeyboardButton(text="🔬 Ilmiy Sifat Tahlili", callback_data="admin_scientific_audit")
        ],
        [
            InlineKeyboardButton(text="📦 Datasetni ZIP Yuklash", callback_data="admin_export_menu"),
            InlineKeyboardButton(text="⚠️ Shubhali Audiolar Nazorati", callback_data="admin_review_flagged")
        ],
        [
            InlineKeyboardButton(text="👥 Foydalanuvchilar & Guruhlar", callback_data="admin_users_menu")
        ],
        [
            InlineKeyboardButton(text="➕ Yangi To'plam Yaratish", callback_data="admin_create_collection"),
            InlineKeyboardButton(text="📝 Matnlar Qo'shish", callback_data="admin_upload_prompts")
        ]
    ])


def get_dataset_export_menu_keyboard(categories: list) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="🤖 uz_robot_cmd (Google Speech Commands ZIP)", callback_data="export_speech_commands_zip")],
        [InlineKeyboardButton(text="📦 Barcha Datasetlar (Umumiy ZIP)", callback_data="export_zip:all")]
    ]
    for cat in categories:
        buttons.append([
            InlineKeyboardButton(text=f"📁 {cat['title']} ni yuklash", callback_data=f"export_zip:cat_{cat['id']}")
        ])
    buttons.append([
        InlineKeyboardButton(text="⬅️ Admin Menyu", callback_data="admin_menu")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_region_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Toshkent", callback_data="set_region:Toshkent"),
            InlineKeyboardButton(text="Samarqand", callback_data="set_region:Samarqand")
        ],
        [
            InlineKeyboardButton(text="Farg'ona", callback_data="set_region:Farg'ona"),
            InlineKeyboardButton(text="Andijon", callback_data="set_region:Andijon"),
            InlineKeyboardButton(text="Namangan", callback_data="set_region:Namangan")
        ],
        [
            InlineKeyboardButton(text="Buxoro", callback_data="set_region:Buxoro"),
            InlineKeyboardButton(text="Qashqadaryo", callback_data="set_region:Qashqadaryo"),
            InlineKeyboardButton(text="Surxondaryo", callback_data="set_region:Surxondaryo")
        ],
        [
            InlineKeyboardButton(text="Xorazm", callback_data="set_region:Xorazm"),
            InlineKeyboardButton(text="Navoiy", callback_data="set_region:Navoiy"),
            InlineKeyboardButton(text="Jizzax", callback_data="set_region:Jizzax")
        ],
        [
            InlineKeyboardButton(text="Sirdaryo", callback_data="set_region:Sirdaryo"),
            InlineKeyboardButton(text="Qoraqalpog'iston", callback_data="set_region:Qoraqalpog'iston"),
            InlineKeyboardButton(text="Boshqa", callback_data="set_region:Boshqa")
        ],
        [
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")
        ]
    ])


def get_device_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📱 Smartfon", callback_data="set_device:smartfon"),
            InlineKeyboardButton(text="🎧 Naushnik / Quloqchin", callback_data="set_device:naushnik")
        ],
        [
            InlineKeyboardButton(text="💻 Noutbuk / Kompyuter", callback_data="set_device:noutbuk"),
            InlineKeyboardButton(text="🎙 Alohida Mikrofon", callback_data="set_device:mikrofon")
        ],
        [
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")
        ]
    ])


def get_admin_users_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👥 Barcha Foydalanuvchilar", callback_data="admin_list_all_users")
        ],
        [
            InlineKeyboardButton(text="👨 Erkak Spikerlar", callback_data="admin_filter:gender_male"),
            InlineKeyboardButton(text="👩 Ayol Spikerlar", callback_data="admin_filter:gender_female")
        ],
        [
            InlineKeyboardButton(text="👶 O'smirlar (18 yoshgacha)", callback_data="admin_filter:age_teen"),
            InlineKeyboardButton(text="🧑 Yoshlar (18-25)", callback_data="admin_filter:age_youth")
        ],
        [
            InlineKeyboardButton(text="👨‍💼 O'rta yosh (26-40)", callback_data="admin_filter:age_adult"),
            InlineKeyboardButton(text="🧓 Katta yosh (40+)", callback_data="admin_filter:age_senior")
        ],
        [
            InlineKeyboardButton(text="🔍 ID yoki Username orqali qidirish", callback_data="admin_search_user")
        ],
        [
            InlineKeyboardButton(text="⬅️ Admin Menyu", callback_data="admin_menu")
        ]
    ])


def get_user_role_toggle_keyboard(user_id: int, current_role: str) -> InlineKeyboardMarkup:
    if current_role in ("admin", "superadmin"):
        btn_text = "🔻 Oddiy foydalanuvchi qilish"
        action = f"set_role:{user_id}:user"
    else:
        btn_text = "👑 Admin qilish"
        action = f"set_role:{user_id}:admin"

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=btn_text, callback_data=action)],
        [InlineKeyboardButton(text="📥 Ushbu foydalanuvchi datasetini yuklash", callback_data=f"export_zip:user_{user_id}")],
        [InlineKeyboardButton(text="⬅️ Foydalanuvchilar menyusi", callback_data="admin_users_menu")]
    ])


def get_speaker_card_keyboard(speaker_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Ushbu spiker datasetini yuklash", callback_data=f"export_zip:speaker_{speaker_id}")],
        [InlineKeyboardButton(text="⬅️ Foydalanuvchilar menyusi", callback_data="admin_users_menu")]
    ])


def get_category_selection_for_upload(categories: list) -> InlineKeyboardMarkup:
    buttons = []
    for cat in categories:
        buttons.append([
            InlineKeyboardButton(text=f"📥 {cat['title']}", callback_data=f"upload_to_cat:{cat['id']}")
        ])
    buttons.append([
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_menu")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_flagged_review_keyboard(recording_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Aslida To'g'ri (Tasdiqlash)", callback_data=f"flag_resolve:{recording_id}:approve"),
            InlineKeyboardButton(text="🗑 Datasetdan O'chirish", callback_data=f"flag_resolve:{recording_id}:reject")
        ],
        [
            InlineKeyboardButton(text="⏩ Keyingisiga o'tish", callback_data="admin_review_flagged"),
            InlineKeyboardButton(text="⬅️ Admin Menyu", callback_data="admin_menu")
        ]
    ])
