import os
from pathlib import Path
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from config import AUDIOS_DIR, SESSION_BATCH_SIZE
from audio_converter import convert_ogg_to_wav, get_exact_wav_duration
from database import (
    get_or_create_user,
    get_speaker,
    get_category,
    get_categories,
    get_next_prompts_for_speaker,
    start_session,
    add_recording,
    complete_session,
    cancel_session,
    set_user_active_category,
    is_admin
)
from keyboards.main_menu import get_main_keyboard, get_recording_keyboard

router = Router()


class RecordingSG(StatesGroup):
    recording_voice = State()


@router.message(F.text == "🎙 Ovoz yozish")
@router.message(Command("record"))
async def start_recording_flow(message: Message, state: FSMContext):
    user = await get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    speaker_id = user.get("active_speaker_id")

    if not speaker_id:
        await message.answer(
            "⚠️ <b>Spiker tanlanmagan!</b>\n\n"
            "Ovoz yozishdan oldin iltimos, o'zingiz yoki yaqiningiz haqidagi ma'lumotlarni kiriting.\n"
            "Buning uchun pastdagi <b>👤 Spikerlarim</b> tugmasini bosing.",
            parse_mode="HTML"
        )
        return

    speaker = await get_speaker(speaker_id)
    if not speaker:
        await message.answer("⚠️ Spiker ma'lumotlari topilmadi. Qaytadan spiker qo'shing.")
        return

    # Foydalanuvchiga qaysi to'plam bo'yicha ovoz yozishni so'raymiz
    categories = await get_categories()
    if not categories:
        await message.answer("⚠️ Hozircha mavjud to'plamlar yo'q.")
        return

    buttons = []
    for cat in categories:
        buttons.append([
            InlineKeyboardButton(text=f"📂 {cat['title']}", callback_data=f"start_rec_cat:{cat['id']}")
        ])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    g_icon = "👨" if speaker["gender"] == "male" else "👩"

    text = (
        f"🎙 <b>Ovoz yozishni boshlash</b>\n\n"
        f"👤 <b>Faol spiker:</b> {g_icon} <b>{speaker['name']}</b> ({speaker['age']} yosh)\n\n"
        "👉 <i>Qaysi to'plam bo'yicha ovoz yozmoqchisiz? Tanlang:</i>"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data.startswith("start_rec_cat:"))
async def handle_start_category_session(callback: CallbackQuery, state: FSMContext):
    cat_id = int(callback.data.split(":")[1])
    user = await get_or_create_user(callback.from_user.id, callback.from_user.username, callback.from_user.first_name)
    speaker_id = user.get("active_speaker_id")

    if not speaker_id:
        await callback.answer("Avval spiker tanlang!", show_alert=True)
        return

    speaker = await get_speaker(speaker_id)
    category = await get_category(cat_id)
    if not category:
        await callback.answer("To'plam topilmadi!", show_alert=True)
        return

    await set_user_active_category(callback.from_user.id, cat_id)

    # Ushbu spiker uchun keyingi matnlarni olamiz
    prompts = await get_next_prompts_for_speaker(speaker_id, cat_id, limit=SESSION_BATCH_SIZE)
    if not prompts:
        await callback.message.edit_text(
            f"ℹ️ <b>{category['title']}</b> to'plamida hozircha yangi matnlar mavjud emas.\n"
            "Iltimos, boshqa to'plamni tanlang yoki ustoz yangi matnlar yuklashini kuting.",
            parse_mode="HTML"
        )
        await callback.answer()
        return

    # Sessiyani bazada boshlaymiz
    session_id = await start_session(
        user_id=callback.from_user.id,
        speaker_id=speaker_id,
        category_id=cat_id,
        batch_size=len(prompts)
    )

    # FSM holatiga yozamiz
    await state.set_state(RecordingSG.recording_voice)
    await state.update_data(
        session_id=session_id,
        speaker_id=speaker_id,
        category_id=cat_id,
        prompts=prompts,
        current_index=0,
        speaker_name=speaker["name"],
        speaker_gender=speaker["gender"],
        speaker_age=speaker["age"],
        category_title=category["title"],
        category_code=category.get("code", "neutral")
    )

    await callback.message.delete()
    await show_current_prompt(callback.message, prompts[0], 0, len(prompts), speaker, category)
    await callback.answer()


async def show_current_prompt(message: Message, prompt: dict, index: int, total: int, speaker: dict, category: dict):
    gender_icon = "👨" if speaker["gender"] == "male" else "👩"
    gender_label = "Erkak" if speaker["gender"] == "male" else "Ayol"

    mood_note = ""
    cat_code = category.get("code", "")
    if cat_code == "happy":
        mood_note = "\n💡 <i>Iltimos, ushbu jumlani quvnoq va xursand kayfiyatda o'qing!</i>"
    elif cat_code == "sad":
        mood_note = "\n💡 <i>Iltimos, ushbu jumlani g'amgin, mahzun yoki yig'lamsirab o'qing!</i>"
    elif cat_code == "angry":
        mood_note = "\n💡 <i>Iltimos, ushbu jumlani jiddiy va g'azab ohangida o'qing!</i>"
    elif cat_code == "commands":
        mood_note = "\n💡 <i>Iltimos, ushbu buyruqni aniq va ravon ayting!</i>"

    text = (
        f"🎙 <b>Ovoz yozish sessiyasi [{index + 1}/{total}]</b>\n\n"
        f"🎭 <b>Toifa:</b> {category['title']}\n"
        f"👤 <b>Spiker:</b> {gender_icon} {speaker['name']} ({gender_label}, {speaker['age']} yosh)\n\n"
        "📖 <b>O'qilishi kerak bo'lgan matn:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👉 <b>« {prompt['text']} »</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━"
        f"{mood_note}\n\n"
        "🎧 <i>Pastdagi mikrofon tugmasini bosib ushlab turing va matnni ovozli xabar qilib yuboring:</i>"
    )

    await message.answer(text, parse_mode="HTML", reply_markup=get_recording_keyboard())


@router.message(RecordingSG.recording_voice, F.text == "❌ Yozishni bekor qilish")
@router.message(RecordingSG.recording_voice, Command("cancel"))
async def cancel_recording_flow(message: Message, state: FSMContext):
    data = await state.get_data()
    session_id = data.get("session_id")
    if session_id:
        await cancel_session(session_id)

    await state.clear()
    admin_status = await is_admin(message.from_user.id)
    kb = get_main_keyboard(is_admin=admin_status)

    await message.answer(
        "❌ <b>Ovoz yozish bekor qilindi.</b>\n\n"
        "⚠️ Qoidaga muvofiq, to'liq yakunlanmagan (chala qolgan) ovozlar asosiy datasetga qo'shilmaydi va bekor qilinadi.\n\n"
        "Istalgan vaqtda qaytadan boshlashingiz mumkin.",
        parse_mode="HTML",
        reply_markup=kb
    )


@router.message(
    RecordingSG.recording_voice,
    F.text.in_([
        "🎙 Ovoz yozish", "👤 Spikerlarim", "📂 To'plamlar", "🎭 Toifalar",
        "📊 Mening hissam", "⚙️ Admin Panel", "🏠 Asosiy menyu"
    ])
)
@router.message(
    RecordingSG.recording_voice,
    Command("start", "record", "speakers", "collections", "categories", "mystats", "admin", "help")
)
async def break_out_of_recording(message: Message, state: FSMContext):
    data = await state.get_data()
    session_id = data.get("session_id")
    if session_id:
        await cancel_session(session_id)
    await state.clear()

    text = message.text or ""
    if text in ("🎙 Ovoz yozish", "/record"):
        await start_recording_flow(message, state)
    elif text in ("👤 Spikerlarim", "/speakers"):
        from handlers.speakers import show_speakers
        await show_speakers(message, state)
    elif text in ("📂 To'plamlar", "🎭 Toifalar", "/collections", "/categories"):
        from handlers.categories import show_categories
        await show_categories(message)
    elif text in ("📊 Mening hissam", "/mystats"):
        from handlers.start import cmd_my_stats
        await cmd_my_stats(message)
    elif text in ("⚙️ Admin Panel", "/admin"):
        from handlers.admin import show_admin_panel
        await show_admin_panel(message)
    else:
        from handlers.start import cmd_start
        await cmd_start(message, state)


@router.callback_query(F.data == "cancel_active_session")
async def callback_cancel_session(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    session_id = data.get("session_id")
    if session_id:
        await cancel_session(session_id)
    await state.clear()
    admin_status = await is_admin(callback.from_user.id)
    kb = get_main_keyboard(is_admin=admin_status)
    await callback.message.edit_text("❌ <b>Ovoz yozish sessiyasi bekor qilindi.</b>", parse_mode="HTML")
    await callback.message.answer("🏠 Asosiy menyudasiz:", reply_markup=kb)
    await callback.answer()


@router.message(RecordingSG.recording_voice, F.voice)
async def process_voice_message(message: Message, state: FSMContext, bot: Bot):
    voice = message.voice
    if voice.duration < 1:
        await message.answer("⚠️ Ovozli xabar juda qisqa (1 soniyadan kam). Iltimos, matnni to'liq o'qib, qaytadan yuboring:")
        return

    data = await state.get_data()
    session_id = data["session_id"]
    speaker_id = data["speaker_id"]
    prompts = data["prompts"]
    current_index = data["current_index"]
    current_prompt = prompts[current_index]

    # Faylni yuklab olish va WAV ga o'tkazish
    speaker_dir = AUDIOS_DIR / f"speaker_{speaker_id}"
    speaker_dir.mkdir(parents=True, exist_ok=True)

    temp_ogg_path = speaker_dir / f"temp_{voice.file_id[-8:]}.ogg"
    wav_file_name = f"sess_{session_id}_p{current_prompt['id']}_{voice.file_id[-8:]}.wav"
    wav_file_path = speaker_dir / wav_file_name

    # Telegramdan ovozni yuklab olamiz
    file_info = await bot.get_file(voice.file_id)
    await bot.download_file(file_info.file_path, destination=temp_ogg_path)

    # OGG faylni toza 16kHz mono WAV formatiga o'tkazamiz
    # Agar buyruqlar toifasi bo'lsa, Google Speech Commands talabiga ko'ra
    # audio aniq 1.0 soniya qilinadi va buyruq markazlashtiriladi
    cat_code = data.get("category_code", "")
    is_command = cat_code in ("robot_cmd", "commands", "unknown_words")

    converted = await convert_ogg_to_wav(
        temp_ogg_path,
        wav_file_path,
        sample_rate=16000,
        remove_ogg=True,
        make_1sec_centered=is_command
    )
    final_name = wav_file_name if converted else f"temp_{voice.file_id[-8:]}.ogg"
    final_file_path = wav_file_path if converted else temp_ogg_path
    actual_file_size = final_file_path.stat().st_size if final_file_path.exists() else (voice.file_size or 0)
    actual_duration = get_exact_wav_duration(final_file_path) if converted else float(voice.duration)

    # Bazaga WAV ma'lumotlarini qo'shamiz
    relative_path = f"audios/speaker_{speaker_id}/{final_name}"
    await add_recording(
        session_id=session_id,
        speaker_id=speaker_id,
        prompt_id=current_prompt["id"],
        file_id=voice.file_id,
        file_path=relative_path,
        duration=actual_duration,
        file_size=actual_file_size
    )

    next_index = current_index + 1
    total = len(prompts)

    if next_index < total:
        # Keyingi matnga o'tish
        await state.update_data(current_index=next_index)
        speaker = {
            "name": data["speaker_name"],
            "gender": data["speaker_gender"],
            "age": data["speaker_age"]
        }
        category = {
            "title": data["category_title"],
            "code": data["category_code"]
        }
        await message.answer(f"✅ <b>{current_index + 1}/{total}</b> ovoz qabul qilindi!", parse_mode="HTML")
        await show_current_prompt(message, prompts[next_index], next_index, total, speaker, category)
    else:
        # Barcha matnlar to'liq o'qib bo'lindi! Sessiyani tasdiqlaymiz!
        await complete_session(session_id)
        await state.clear()

        admin_status = await is_admin(message.from_user.id)
        kb = get_main_keyboard(is_admin=admin_status)

        text = (
            "🎉 <b>BARAKALLA! SIZ TO'PLAMNI TO'LIQ YAKUNLADINGIZ!</b>\n\n"
            f"✨ Ushbu sessiyadagi barcha <b>{total} ta matn</b> muvaffaqiyatli o'qildi va audio fayllar to'liq saqlandi.\n"
            f"👤 <b>Spiker:</b> {data['speaker_name']} ({data['speaker_age']} yosh)\n"
            f"🎭 <b>Toifa:</b> {data['category_title']}\n\n"
            "✅ <b>Ovozlar to'liq tekshirilib, asosiy dataset arxiviga kiritildi!</b>\n\n"
            "🤝 O'zbek tili sun'iy intellekt modelini o'qitishga qo'shgan beminnat hissangiz uchun <b>KATTA RAHMAT!</b>\n\n"
            "Yana davom ettirish uchun pastdagi <b>🎙 Ovoz yozish</b> tugmasini bosishingiz mumkin."
        )
        await message.answer(text, parse_mode="HTML", reply_markup=kb)


@router.message(RecordingSG.recording_voice)
async def process_wrong_message_during_recording(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Sessiyani bekor qilish", callback_data="cancel_active_session")]
    ])
    await message.answer(
        "⚠️ <b>Iltimos, faqat ovozli xabar (Voice) yuboring!</b>\n"
        "Matnni o'qib, pastdagi mikrofon tugmasini bosib turing.\n\n"
        "Jarayonni to'xtatmoqchi bo'lsangiz, pastdagi tugmani bosing:",
        parse_mode="HTML",
        reply_markup=kb
    )


@router.message(F.voice)
async def process_voice_outside_session(message: Message):
    await message.answer(
        "ℹ️ <b>Ovoz qabul qilinmadi!</b>\n\n"
        "Ovoz yozishni boshlash uchun avval pastdagi <b>🎙 Ovoz yozish</b> tugmasini bosing va kerakli to'plamni tanlang.",
        parse_mode="HTML"
    )


@router.message()
async def process_unhandled_message(message: Message):
    admin_status = await is_admin(message.from_user.id)
    kb = get_main_keyboard(is_admin=admin_status)
    await message.answer(
        "ℹ️ Buyruq tushunarsiz.\n\n"
        "Kerakli bo'limni tanlash uchun quyidagi menyu tugmalaridan foydalaning:",
        parse_mode="HTML",
        reply_markup=kb
    )
