from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from database import (
    get_or_create_user,
    get_categories,
    get_category,
    set_user_active_category,
    get_prompts_count
)
from keyboards.inline import get_categories_inline_keyboard

router = Router()


@router.message(F.text == "📂 To'plamlar")
@router.message(F.text == "🎭 Toifalar")
@router.message(Command("collections"))
@router.message(Command("categories"))
@router.message(Command("category"))
async def show_categories(message: Message, state: FSMContext = None):
    if state:
        await state.clear()
    user = await get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    categories = await get_categories()
    active_cat_id = user.get("active_category_id")

    text = (
        "📂 <b>Dataset To'plamlari:</b>\n\n"
        "Ovoz yozish mumkin bo'lgan to'plamlar ro'yxati:\n\n"
        "• <b>📖 Kitobiy / Neytral:</b> Ovozni matnga aylantirish (ASR/STT) uchun xolis o'qish;\n"
        "• <b>😊 Quvnoq / Xursand:</b> Ko'tarinki kayfiyatdagi ovoz modeli uchun;\n"
        "• <b>😢 Yig'lamsirab / Mahzun:</b> Hissiyotli va g'amgin ovoz modeli uchun;\n"
        "• <b>😠 G'azab / Asabiy:</b> Kuchli jiddiylik va g'azab ohangidagi ovoz;\n"
        "• <b>🗣 Buyruqlar:</b> Smart-uy va robot yordamchilar uchun.\n\n"
        "To'plamlardan birini tanlashingiz mumkin (shuningdek, 🎙 Ovoz yozish bosilganda ham to'plam so'raladi):"
    )
    kb = get_categories_inline_keyboard(categories, active_cat_id)
    await message.answer(text, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data.startswith("select_category:"))
async def handle_select_category(callback: CallbackQuery):
    cat_id = int(callback.data.split(":")[1])
    cat = await get_category(cat_id)
    if not cat:
        await callback.answer("Toifa topilmadi!", show_alert=True)
        return

    await set_user_active_category(callback.from_user.id, cat_id)
    categories = await get_categories()
    kb = get_categories_inline_keyboard(categories, cat_id)

    p_count = await get_prompts_count(cat_id)

    await callback.message.edit_text(
        f"✅ <b>Faol toifa tanlandi:</b>\n\n"
        f"<b>{cat['title']}</b>\n"
        f"<i>{cat['description']}</i>\n\n"
        f"📚 Ushbu toifada jami <b>{p_count} ta</b> matn mavjud.\n\n"
        "Endi <b>🎙 Ovoz yozish</b> tugmasini bosib, ushbu yo'nalishda ovoz yozishingiz mumkin!",
        parse_mode="HTML",
        reply_markup=kb
    )
    await callback.answer("Toifa tanlandi!")
