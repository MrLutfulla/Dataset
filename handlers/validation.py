import logging
import html
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from config import BASE_DIR
from database import (
    get_or_create_user,
    get_next_recording_for_validation,
    add_validation,
    is_admin
)
from keyboards.main_menu import get_main_keyboard

logger = logging.getLogger(__name__)
router = Router()


async def send_validation_prompt(chat_id: int, user_id: int, bot: Bot, state: FSMContext, exclude_ids: list = None):
    """Boshqa foydalanuvchilarning ovozini anonim tarzda tekshirishga taqdim etadi"""
    data = await state.get_data()
    current_excludes = data.get("val_excludes", [])
    if exclude_ids:
        current_excludes.extend(exclude_ids)
        current_excludes = list(set(current_excludes))
        await state.update_data(val_excludes=current_excludes)

    rec = await get_next_recording_for_validation(user_id, exclude_ids=current_excludes)
    admin_status = await is_admin(user_id)
    kb_main = get_main_keyboard(is_admin=admin_status)

    if not rec:
        await bot.send_message(
            chat_id=chat_id,
            text=(
                "🎉 <b>Boshqa ishtirokchilarning barcha ovozlarini tekshirib bo'ldingiz!</b>\n\n"
                "🔒 <b>Taqsimlash qoidasi:</b>\n"
                "• Tizimda hech kimga o'zi yozgan ovoz tekshirish uchun berilmaydi;\n"
                "• Siz yozgan ovozlar xolis baholanishi uchun boshqa ishtirokchilarga yuboriladi;\n"
                "• Boshqa ishtirokchilar yangi ovoz yozishi bilan ular yana sizga tekshirish uchun navbat bilan beriladi.\n\n"
                "<i>Dataset sifatini oshirishga qo'shgan hissangiz uchun katta rahmat!</i>"
            ),
            parse_mode="HTML",
            reply_markup=kb_main
        )
        await state.clear()
        return

    # Faqat Diktor ID si ko'rsatiladi, qolgan barcha ma'lumotlar maxfiy (sir) saqlanadi
    spk_tag = f"spk{rec['speaker_id']:03d}"

    caption = (
        "🎧 <b>Ovozni tinglang va baholang:</b>\n\n"
        "📖 <b>O'qilishi kerak bo'lgan matn:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👉 <b>« {html.escape(rec['prompt_text'])} »</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🏷 <b>Diktor ID:</b> <code>{spk_tag}</code>\n\n"
        "👇 <i>Ovoz yuqoridagi matnga to'liq mos va sifatli aytilganmi? Tanlang:</i>"
    )

    rec_id = rec["recording_id"]
    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ To'g'ri (mos)", callback_data=f"val_vote:{rec_id}:correct"),
            InlineKeyboardButton(text="❌ Noto'g'ri", callback_data=f"val_vote:{rec_id}:incorrect")
        ],
        [
            InlineKeyboardButton(text="⚠️ Sifati past (shovqinli)", callback_data=f"val_vote:{rec_id}:low_quality")
        ],
        [
            InlineKeyboardButton(text="⏩ O'tkazib yuborish", callback_data=f"val_skip:{rec_id}"),
            InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="val_exit")
        ]
    ])

    file_id = rec.get("file_id")
    file_path = BASE_DIR / rec["file_path"]

    sent = False
    if file_id:
        try:
            await bot.send_voice(
                chat_id=chat_id,
                voice=file_id,
                caption=caption,
                parse_mode="HTML",
                reply_markup=inline_kb
            )
            sent = True
        except Exception as e:
            logger.warning(f"Voice file_id orqali yuborishda xato: {e}")
            sent = False

    if not sent and file_path.exists():
        try:
            await bot.send_voice(
                chat_id=chat_id,
                voice=FSInputFile(file_path),
                caption=caption,
                parse_mode="HTML",
                reply_markup=inline_kb
            )
            sent = True
        except Exception as e:
            logger.error(f"FSInputFile orqali yuborishda xato: {e}")

    if not sent:
        # Fayl topilmasa, keyingi audioga o'tamiz
        await send_validation_prompt(chat_id, user_id, bot, state, exclude_ids=[rec_id])


@router.message(F.text == "🎧 Ovoz tekshirish")
@router.message(Command("validate"))
@router.message(Command("check"))
@router.message(Command("verify"))
async def start_validation_flow(message: Message, state: FSMContext, bot: Bot):
    user = await get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    await state.clear()
    await message.answer(
        "🎧 <b>Ovoz tekshirish (Crowdsourced Validation)</b>\n\n"
        "Dataset sifatini oshirish uchun boshqa foydalanuvchilar o'qigan ovozlarni tinglab baholang.\n"
        "🔒 <b>Maxfiylik:</b> Barcha ma'lumotlar anonim (shaxsiy ism va profil sir saqlanadi).\n\n"
        "Ovoz yuklanmoqda...",
        parse_mode="HTML"
    )
    await send_validation_prompt(message.chat.id, message.from_user.id, bot, state)


@router.callback_query(F.data.startswith("val_vote:"))
async def handle_validation_vote(callback: CallbackQuery, state: FSMContext, bot: Bot):
    parts = callback.data.split(":")
    rec_id = int(parts[1])
    status = parts[2]

    # Bazaga tekshiruv natijasini saqlash
    await add_validation(rec_id, callback.from_user.id, status)

    status_labels = {
        "correct": "✅ To'g'ri deb tasdiqlandi! Rahmat!",
        "incorrect": "❌ Noto'g'ri deb belgilandi! Rahmat!",
        "low_quality": "⚠️ Sifati past deb belgilandi! Rahmat!"
    }
    toast_msg = status_labels.get(status, "Qabul qilindi!")
    await callback.answer(toast_msg, show_alert=False)

    # Oldingi xabardagi tugmalarni olib tashlaymiz
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    # Keyingi ovozga o'tish
    await send_validation_prompt(callback.message.chat.id, callback.from_user.id, bot, state, exclude_ids=[rec_id])


@router.callback_query(F.data.startswith("val_skip:"))
async def handle_validation_skip(callback: CallbackQuery, state: FSMContext, bot: Bot):
    parts = callback.data.split(":")
    rec_id = int(parts[1])

    await callback.answer("⏩ O'tkazib yuborildi.")
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    await send_validation_prompt(callback.message.chat.id, callback.from_user.id, bot, state, exclude_ids=[rec_id])


@router.callback_query(F.data == "val_exit")
async def handle_validation_exit(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    admin_status = await is_admin(callback.from_user.id)
    kb_main = get_main_keyboard(is_admin=admin_status)

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    await callback.message.answer("🏠 Asosiy menyudasiz. Kerakli bo'limni tanlang:", reply_markup=kb_main)
    await callback.answer("Menyuga qaytildi.")
