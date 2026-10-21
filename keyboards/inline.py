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
            InlineKeyboardButton(text="📦 Datasetni ZIP Yuklash", callback_data="admin_export_menu")
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
            InlineKeyboardButton(text="👶 O'smirlar (<18)", callback_data="admin_filter:age_teen"),
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
