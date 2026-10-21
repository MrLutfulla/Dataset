from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from database import (
    get_or_create_user,
    get_user,
    get_speakers_by_user,
    create_speaker,
    set_user_active_speaker,
    get_speaker
)
from keyboards.inline import (
    get_speakers_inline_keyboard,
    get_gender_inline_keyboard
)

router = Router()


class AddSpeakerSG(StatesGroup):
    waiting_for_name = State()
    waiting_for_gender = State()
    waiting_for_age = State()


@router.message(F.text == "👤 Spikerlarim")
@router.message(Command("speakers"))
async def show_speakers(message: Message):
    user = await get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    speakers = await get_speakers_by_user(message.from_user.id)
    active_id = user.get("active_speaker_id")

    if not speakers:
        text = (
            "👤 <b>Sizda hali birorta spiker qo'shilmagan!</b>\n\n"
            "Ovoz yozishdan oldin spiker (o'zingiz yoki yaqiningiz) haqida qisqa ma'lumot kiritishingiz kerak.\n"
            "Bu model uchun ovoz kimga tegishli ekanligini (jinsi, yoshi) to'g'ri o'rganishga zarur.\n\n"
            "Quyidagi tugmani bosing:"
        )
    else:
        text = (
            "👤 <b>Sizning spikerlaringiz ro'yxati:</b>\n\n"
            "Ayni paytda faol bo'lgan spiker yonida '✅' belgisi turadi. "
            "Boshqa spikerni tanlash uchun ustiga bosing yoki yangi odam qo'shing:"
        )

    kb = get_speakers_inline_keyboard(speakers, active_id)
    await message.answer(text, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data.startswith("select_speaker:"))
async def handle_select_speaker(callback: CallbackQuery):
    speaker_id = int(callback.data.split(":")[1])
    sp = await get_speaker(speaker_id)
    if not sp:
        await callback.answer("Spiker topilmadi!", show_alert=True)
        return

    await set_user_active_speaker(callback.from_user.id, speaker_id)
    speakers = await get_speakers_by_user(callback.from_user.id)
    kb = get_speakers_inline_keyboard(speakers, speaker_id)

    g_icon = "👨" if sp["gender"] == "male" else "👩"
    await callback.message.edit_text(
        f"✅ <b>Faol spiker o'zgartirildi:</b>\n"
        f"{g_icon} <b>{sp['name']}</b> ({sp['age']} yosh)\n\n"
        "Endi yoziladigan ovozlar aynan ushbu inson nomiga biriktiriladi.",
        parse_mode="HTML",
        reply_markup=kb
    )
    await callback.answer("Tanlandi!")


@router.callback_query(F.data == "add_speaker")
async def start_add_speaker(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddSpeakerSG.waiting_for_name)
    await callback.message.answer(
        "📝 <b>Yangi spiker qo'shish</b>\n\n"
        "Iltimos, ushbu insonning <b>Ismini</b> (yoki laqabini) kiriting:\n"
        "<i>Masalan: Sardor, Madina yoki Ukam Ali</i>",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AddSpeakerSG.waiting_for_name)
async def process_speaker_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2 or len(name) > 40:
        await message.answer("Iltimos, 2 tadan 40 tagacha belgidan iborat to'g'ri ism kiriting:")
        return

    await state.update_data(name=name)
    await state.set_state(AddSpeakerSG.waiting_for_gender)
    await message.answer(
        f"👤 Spiker: <b>{name}</b>\n\n"
        "Endi ushbu shaxsning <b>Jinsini</b> tanlang:",
        parse_mode="HTML",
        reply_markup=get_gender_inline_keyboard()
    )


@router.callback_query(AddSpeakerSG.waiting_for_gender, F.data.startswith("set_gender:"))
async def process_speaker_gender(callback: CallbackQuery, state: FSMContext):
    gender = callback.data.split(":")[1]
    await state.update_data(gender=gender)
    await state.set_state(AddSpeakerSG.waiting_for_age)
    await callback.message.edit_text(
        "🎂 Endi ushbu insonning <b>Yoshini</b> kiriting (faqat raqam):\n"
        "<i>Masalan: 16, 21 yoki 35</i>",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AddSpeakerSG.waiting_for_age)
async def process_speaker_age(message: Message, state: FSMContext):
    val = message.text.strip()
    if not val.isdigit() or int(val) < 5 or int(val) > 100:
        await message.answer("Iltimos, haqiqiy yoshni kiriting (5 dan 100 gacha son bo'lsin):")
        return

    age = int(val)
    data = await state.get_data()
    name = data["name"]
    gender = data["gender"]

    speaker_id = await create_speaker(
        user_id=message.from_user.id,
        name=name,
        gender=gender,
        age=age
    )
    await state.clear()

    g_icon = "👨 Erkak" if gender == "male" else "👩 Ayol"
    await message.answer(
        f"🎉 <b>Yangi spiker muvaffaqiyatli saqlandi va faol qilindi!</b>\n\n"
        f"• <b>Ismi:</b> {name}\n"
        f"• <b>Jinsi:</b> {g_icon}\n"
        f"• <b>Yoshi:</b> {age} yosh\n\n"
        "Endi <b>🎙 Ovoz yozish</b> tugmasini bosib, ovoz yozishni boshlashingiz mumkin!",
        parse_mode="HTML"
    )


@router.callback_query(F.data == "cancel_action")
async def cancel_action_cb(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.answer("Bekor qilindi.")
