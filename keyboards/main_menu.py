from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    keyboard = [
        [
            KeyboardButton(text="🎙 Ovoz yozish"),
            KeyboardButton(text="👤 Spikerlarim")
        ],
        [
            KeyboardButton(text="📂 To'plamlar"),
            KeyboardButton(text="📊 Mening hissam")
        ]
    ]
    if is_admin:
        keyboard.append([KeyboardButton(text="⚙️ Admin Panel")])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        is_persistent=True
    )


def get_recording_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Yozishni bekor qilish")]
        ],
        resize_keyboard=True
    )
