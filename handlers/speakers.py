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
    get_speaker,
    compute_age_group,
    is_admin
)
from keyboards.main_menu import get_main_keyboard
from keyboards.inline import (
    get_speakers_inline_keyboard,
    get_gender_inline_keyboard,
    get_region_inline_keyboard,
    get_device_inline_keyboard
)

router = Router()


class AddSpeakerSG(StatesGroup):
    waiting_for_name = State()
    waiting_for_gender = State()
    waiting_for_age = State()
    waiting_for_region = State()
    waiting_for_device = State()


@router.message(F.text == "👤 Spikerlarim")
@router.message(Command("speakers"))
async def show_speakers(message: Message, state: FSMContext):
    data = await state.get_data()
    session_id = data.get("session_id")
    if session_id:
        from database import cancel_session
        await cancel_session(session_id)
    await state.clear()

    user = await get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    speakers = await get_speakers_by_user(message.from_user.id)
    active_id = user.get("active_speaker_id")

    if not speakers:
        text = (
            "👤 <b>Sizda hali birorta spiker qo'shilmagan!</b>\n\n"
            "Google Speech Commands standarti bo'yicha har bir diktorning "
            "<b>jinsi, yosh guruhi, hududi va qurilmasi</b> saqlanadi.\n\n"
            "Quyidagi tugmani bosing va birinchi spikerni qo'shing:"
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

    g_icon = "👨" if sp["gender"] in ("male", "erkak") else "👩"
    spk_tag = f"spk{sp['id']:03d}"
    await callback.message.edit_text(
        f"✅ <b>Faol spiker o'zgartirildi:</b>\n"
        f"🏷 <b>ID:</b> <code>{spk_tag}</code>\n"
        f"{g_icon} <b>{sp['name']}</b> ({sp['age']} yosh, {sp.get('region', 'Toshkent')})\n"
        f"📱 Qurilma: <i>{sp.get('device', 'smartfon')}</i>\n\n"
        "Endi yoziladigan ovozlar aynan ushbu diktor nomiga biriktiriladi.",
        parse_mode="HTML",
        reply_markup=kb
    )
    await callback.answer("Tanlandi!")


@router.callback_query(F.data == "add_speaker")
async def start_add_speaker(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddSpeakerSG.waiting_for_name)
    await callback.message.answer(
        "📝 <b>Yangi spiker qo'shish (1/5)</b>\n\n"
        "Iltimos, ushbu insonning <b>Ismini</b> (yoki laqabini) kiriting:\n"
        "<i>Masalan: Sardor, Madina yoki spk01</i>",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AddSpeakerSG.waiting_for_name)
async def process_speaker_name(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Iltimos, matn ko'rinishida ism kiriting:")
        return

    name = message.text.strip()
    if name.startswith("/") or name in ("❌ Bekor qilish", "🏠 Asosiy menyu", "🎙 Ovoz yozish", "👤 Spikerlarim", "📂 To'plamlar", "📊 Mening hissam"):
        await state.clear()
        await message.answer("❌ Spiker qo'shish bekor qilindi.")
        return

    if len(name) < 2 or len(name) > 40:
        await message.answer("Iltimos, 2 tadan 40 tagacha belgidan iborat to'g'ri ism kiriting:")
        return

    await state.update_data(name=name)
    await state.set_state(AddSpeakerSG.waiting_for_gender)
    await message.answer(
        f"👤 Spiker: <b>{name}</b>\n\n"
        "<b>(2/5)</b> Ushbu shaxsning <b>Jinsini</b> tanlang:",
        parse_mode="HTML",
        reply_markup=get_gender_inline_keyboard()
    )


@router.callback_query(AddSpeakerSG.waiting_for_gender, F.data.startswith("set_gender:"))
async def process_speaker_gender(callback: CallbackQuery, state: FSMContext):
    gender = callback.data.split(":")[1]
    await state.update_data(gender=gender)
    await state.set_state(AddSpeakerSG.waiting_for_age)
    await callback.message.edit_text(
        "🎂 <b>(3/5)</b> Ushbu insonning <b>Yoshini</b> kiriting (faqat raqam):\n"
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
    age_group = compute_age_group(age)
    await state.update_data(age=age, age_group=age_group)
    await state.set_state(AddSpeakerSG.waiting_for_region)

    await message.answer(
        f"🎂 Yoshi: <b>{age}</b> (Yosh guruhi: <code>{age_group}</code>)\n\n"
        "📍 <b>(4/5)</b> Qaysi <b>Hududdansiz</b>? Tanlang:",
        parse_mode="HTML",
        reply_markup=get_region_inline_keyboard()
    )


@router.callback_query(AddSpeakerSG.waiting_for_region, F.data.startswith("set_region:"))
async def process_speaker_region(callback: CallbackQuery, state: FSMContext):
    region = callback.data.split(":")[1]
    await state.update_data(region=region)
    await state.set_state(AddSpeakerSG.waiting_for_device)

    await callback.message.edit_text(
        f"📍 Hudud: <b>{region}</b>\n\n"
        "📱 <b>(5/5)</b> Qaysi <b>Qurilmadan</b> ovoz yozasiz? Tanlang:",
        parse_mode="HTML",
        reply_markup=get_device_inline_keyboard()
    )
    await callback.answer()


@router.callback_query(AddSpeakerSG.waiting_for_device, F.data.startswith("set_device:"))
async def process_speaker_device(callback: CallbackQuery, state: FSMContext):
    device = callback.data.split(":")[1]
    data = await state.get_data()
    name = data["name"]
    gender = data["gender"]
    age = data["age"]
    age_group = data["age_group"]
    region = data["region"]

    # Foydalanuvchida avval spiker bo'lgan-bo'lmaganini tekshiramiz
    existing_speakers = await get_speakers_by_user(callback.from_user.id)
    is_first_speaker = len(existing_speakers) == 0

    speaker_id = await create_speaker(
        user_id=callback.from_user.id,
        name=name,
        gender=gender,
        age=age,
        region=region,
        device=device,
        age_group=age_group
    )
    await state.clear()

    g_icon = "👨 Erkak" if gender in ("male", "erkak") else "👩 Ayol"
    spk_tag = f"spk{speaker_id:03d}"

    admin_status = await is_admin(callback.from_user.id)
    kb = get_main_keyboard(is_admin=admin_status)

    if is_first_speaker:
        text = (
            f"🎉 <b>Tabriklaymiz, siz muvaffaqiyatli ro'yxatdan o'tdingiz!</b>\n\n"
            f"🏷 <b>Diktor ID:</b> <code>{spk_tag}</code>\n"
            f"👤 <b>Ismi:</b> {name}\n"
            f"🚻 <b>Jinsi:</b> {g_icon}\n"
            f"🎂 <b>Yoshi:</b> {age} yosh (Guruh: <code>{age_group}</code>)\n"
            f"📍 <b>Hudud:</b> {region}\n"
            f"📱 <b>Qurilma:</b> {device}\n\n"
            "✅ <i>Boshlang'ich diktor profilingiz faol holatga keltirildi.</i>\n\n"
            "Endi quyidagi menyudan <b>🎙 Ovoz yozish</b> tugmasini bosib robot buyruqlarini yozishni boshlashingiz mumkin.\n\n"
            "💡 <i>Eslatma: Keyinchalik boshqa insonlar (oila a'zolaringiz yoki do'stlaringiz) nomidan ham ovoz yozmoqchi bo'lsangiz, "
            "<b>👤 Spikerlarim</b> bo'limi orqali yangi spikerlarni qo'shishingiz mumkin.</i>"
        )
    else:
        text = (
            f"🎉 <b>Yangi spiker muvaffaqiyatli saqlandi!</b>\n\n"
            f"🏷 <b>Diktor ID:</b> <code>{spk_tag}</code>\n"
            f"👤 <b>Ismi:</b> {name}\n"
            f"🚻 <b>Jinsi:</b> {g_icon}\n"
            f"🎂 <b>Yoshi:</b> {age} yosh (Guruh: <code>{age_group}</code>)\n"
            f"📍 <b>Hudud:</b> {region}\n"
            f"📱 <b>Qurilma:</b> {device}\n\n"
            "✅ <i>Ushbu spiker faol holatga keltirildi. Endi yoziladigan ovozlar aynan ushbu diktor nomiga biriktiriladi!</i>"
        )

    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.message.answer("🏠 Asosiy menyu ochildi. Kerakli bo'limni tanlang:", reply_markup=kb)
    await callback.answer("Saqlandi!")


@router.callback_query(F.data == "cancel_action")
async def cancel_action_cb(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    speakers = await get_speakers_by_user(callback.from_user.id)
    if not speakers:
        await callback.message.answer(
            "⚠️ Ovoz yozish va tizimdan to'liq foydalanish uchun kamida 1 ta spiker ro'yxatdan o'tishi kerak.\n\n"
            "Ro'yxatdan o'tish uchun /start buyrug'ini bosing."
        )
    else:
        admin_status = await is_admin(callback.from_user.id)
        await callback.message.answer("❌ Bekor qilindi.", reply_markup=get_main_keyboard(is_admin=admin_status))
    await callback.answer("Bekor qilindi.")
