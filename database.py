import aiosqlite
from contextlib import asynccontextmanager
from datetime import datetime
from config import DB_PATH
from default_prompts import DEFAULT_CATEGORIES, DEFAULT_PROMPTS


@asynccontextmanager
async def get_db():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db


async def init_db():
    async with get_db() as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                role TEXT DEFAULT 'user',
                active_speaker_id INTEGER,
                active_category_id INTEGER,
                created_at TEXT
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS speakers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT NOT NULL,
                gender TEXT NOT NULL,
                age INTEGER NOT NULL,
                created_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                is_active INTEGER DEFAULT 1
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                speaker_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                batch_size INTEGER DEFAULT 5,
                status TEXT DEFAULT 'in_progress',
                created_at TEXT,
                completed_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (speaker_id) REFERENCES speakers (id),
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS recordings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                speaker_id INTEGER NOT NULL,
                prompt_id INTEGER NOT NULL,
                file_id TEXT,
                file_path TEXT NOT NULL,
                duration REAL DEFAULT 0,
                file_size INTEGER DEFAULT 0,
                created_at TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions (id),
                FOREIGN KEY (speaker_id) REFERENCES speakers (id),
                FOREIGN KEY (prompt_id) REFERENCES prompts (id)
            )
        """)

        await db.commit()

        # Migratsiyalar: speakers jadvaliga yangi ustunlar
        spk_cols_cursor = await db.execute("PRAGMA table_info(speakers)")
        spk_cols = [row["name"] for row in await spk_cols_cursor.fetchall()]
        if "region" not in spk_cols:
            await db.execute("ALTER TABLE speakers ADD COLUMN region TEXT DEFAULT 'Toshkent'")
        if "device" not in spk_cols:
            await db.execute("ALTER TABLE speakers ADD COLUMN device TEXT DEFAULT 'smartfon'")
        if "environment" not in spk_cols:
            await db.execute("ALTER TABLE speakers ADD COLUMN environment TEXT DEFAULT 'xona'")
        if "age_group" not in spk_cols:
            await db.execute("ALTER TABLE speakers ADD COLUMN age_group TEXT DEFAULT '18-25'")

        # Toifalarni tekshirish va yangilarini qo'shish (DEFAULT_CATEGORIES)
        for cat in DEFAULT_CATEGORIES:
            check_cat = await db.execute("SELECT id FROM categories WHERE code = ?", (cat["code"],))
            cat_row = await check_cat.fetchone()
            if not cat_row:
                cursor_ins = await db.execute(
                    "INSERT INTO categories (code, title, description) VALUES (?, ?, ?)",
                    (cat["code"], cat["title"], cat["description"])
                )
                cat_id = cursor_ins.lastrowid
                prompts_list = DEFAULT_PROMPTS.get(cat["code"], [])
                for p_text in prompts_list:
                    await db.execute(
                        "INSERT INTO prompts (category_id, text) VALUES (?, ?)",
                        (cat_id, p_text)
                    )
            else:
                cat_id = cat_row["id"]
                # Mavjud toifada yangi matnlar bo'lsa ularni ham kiritish
                prompts_list = DEFAULT_PROMPTS.get(cat["code"], [])
                for p_text in prompts_list:
                    chk_p = await db.execute("SELECT id FROM prompts WHERE category_id = ? AND text = ?", (cat_id, p_text))
                    if not await chk_p.fetchone():
                        await db.execute(
                            "INSERT INTO prompts (category_id, text) VALUES (?, ?)",
                            (cat_id, p_text)
                        )
        await db.commit()


# ==================== USERS ====================

async def get_or_create_user(user_id: int, username: str = None, first_name: str = None):
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = await cursor.fetchone()
        if not user:
            # Agar bazada birinchi foydalanuvchi bo'lsa, uni avtomatik superadmin qilamiz!
            count_cur = await db.execute("SELECT COUNT(*) as cnt FROM users")
            total_users = (await count_cur.fetchone())["cnt"]
            initial_role = "admin" if total_users == 0 else "user"

            # Default category neutral ni olamiz
            cat_cur = await db.execute("SELECT id FROM categories WHERE code = 'neutral' LIMIT 1")
            cat_row = await cat_cur.fetchone()
            default_cat_id = cat_row["id"] if cat_row else 1

            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            await db.execute(
                "INSERT INTO users (user_id, username, first_name, role, active_category_id, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, username, first_name, initial_role, default_cat_id, now)
            )
            await db.commit()
            cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user = await cursor.fetchone()
        else:
            # Username yoki first_name o'zgargan bo'lsa yangilash
            if user["username"] != username or user["first_name"] != first_name:
                await db.execute(
                    "UPDATE users SET username = ?, first_name = ? WHERE user_id = ?",
                    (username, first_name, user_id)
                )
                await db.commit()
        return dict(user)


async def get_user(user_id: int):
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = await cursor.fetchone()
        return dict(user) if user else None


async def is_admin(user_id: int) -> bool:
    user = await get_user(user_id)
    return user is not None and user.get("role") in ("admin", "superadmin")


async def set_user_role(user_id: int, role: str):
    async with get_db() as db:
        await db.execute("UPDATE users SET role = ? WHERE user_id = ?", (role, user_id))
        await db.commit()


async def find_users_by_query(query: str):
    query = query.strip().lstrip("@")
    async with get_db() as db:
        if query.isdigit():
            cursor = await db.execute("SELECT * FROM users WHERE user_id = ? OR username LIKE ?", (int(query), f"%{query}%"))
        else:
            cursor = await db.execute("SELECT * FROM users WHERE username LIKE ? OR first_name LIKE ?", (f"%{query}%", f"%{query}%"))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_all_users(limit: int = 50):
    async with get_db() as db:
        cursor = await db.execute(
            """
            SELECT u.*, 
                   COUNT(DISTINCT s.id) as speakers_count,
                   COUNT(DISTINCT sess.id) as completed_sessions
            FROM users u
            LEFT JOIN speakers s ON u.user_id = s.user_id
            LEFT JOIN sessions sess ON u.user_id = sess.user_id AND sess.status = 'completed'
            GROUP BY u.user_id
            ORDER BY u.created_at DESC
            LIMIT ?
            """,
            (limit,)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def set_user_active_speaker(user_id: int, speaker_id: int):
    async with get_db() as db:
        await db.execute("UPDATE users SET active_speaker_id = ? WHERE user_id = ?", (speaker_id, user_id))
        await db.commit()


async def set_user_active_category(user_id: int, category_id: int):
    async with get_db() as db:
        await db.execute("UPDATE users SET active_category_id = ? WHERE user_id = ?", (category_id, user_id))
        await db.commit()


# ==================== SPEAKERS ====================

def compute_age_group(age: int) -> str:
    """Yosh guruhini aniqlash (<18, 18-25, 26-40, 40+)"""
    if age < 18:
        return "<18"
    elif 18 <= age <= 25:
        return "18-25"
    elif 26 <= age <= 40:
        return "26-40"
    else:
        return "40+"


async def create_speaker(
    user_id: int,
    name: str,
    gender: str,
    age: int,
    region: str = "Toshkent",
    device: str = "smartfon",
    environment: str = "xona",
    age_group: str = None
):
    if not age_group:
        age_group = compute_age_group(age)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    async with get_db() as db:
        cursor = await db.execute(
            """
            INSERT INTO speakers (user_id, name, gender, age, region, device, environment, age_group, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, name, gender, age, region, device, environment, age_group, now)
        )
        speaker_id = cursor.lastrowid
        # Avtomatik faol spiker qilib belgilash
        await db.execute("UPDATE users SET active_speaker_id = ? WHERE user_id = ?", (speaker_id, user_id))
        await db.commit()
        return speaker_id


async def get_speakers_by_user(user_id: int):
    async with get_db() as db:
        cursor = await db.execute(
            """
            SELECT s.*, 
                   COUNT(DISTINCT r.id) as recordings_count
            FROM speakers s
            LEFT JOIN recordings r ON s.id = r.speaker_id
            LEFT JOIN sessions sess ON r.session_id = sess.id AND sess.status = 'completed'
            WHERE s.user_id = ?
            GROUP BY s.id
            ORDER BY s.id DESC
            """,
            (user_id,)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_speaker(speaker_id: int):
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM speakers WHERE id = ?", (speaker_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


# ==================== CATEGORIES ====================

async def get_categories():
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM categories WHERE is_active = 1 ORDER BY id ASC")
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_category(category_id: int):
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM categories WHERE id = ?", (category_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def add_category(code: str, title: str, description: str):
    if not code:
        import re
        base = re.sub(r"[^a-zA-Z0-9]+", "_", title.lower()).strip("_")
        code = f"{base}_{int(datetime.now().timestamp())}"
    async with get_db() as db:
        cursor = await db.execute(
            "INSERT INTO categories (code, title, description) VALUES (?, ?, ?)",
            (code, title, description)
        )
        await db.commit()
        return cursor.lastrowid


# ==================== PROMPTS ====================

async def add_prompts_bulk(category_id: int, texts: list[str]):
    async with get_db() as db:
        count = 0
        for text in texts:
            t = text.strip()
            if t:
                await db.execute("INSERT INTO prompts (category_id, text) VALUES (?, ?)", (category_id, t))
                count += 1
        await db.commit()
        return count


async def get_prompts_count(category_id: int):
    async with get_db() as db:
        cursor = await db.execute("SELECT COUNT(*) as cnt FROM prompts WHERE category_id = ? AND is_active = 1", (category_id,))
        row = await cursor.fetchone()
        return row["cnt"] if row else 0


async def get_next_prompts_for_speaker(speaker_id: int, category_id: int, limit: int = 5):
    """
    Spiker hali yakunlangan sessiyalarda o'qimagan matnlarni olib beradi.
    Agar barcha matnlar tugagan bo'lsa, ixtiyoriy matnlardan aylantirib beradi.
    """
    async with get_db() as db:
        cursor = await db.execute(
            """
            SELECT p.* FROM prompts p
            WHERE p.category_id = ? AND p.is_active = 1
              AND p.id NOT IN (
                  SELECT r.prompt_id FROM recordings r
                  JOIN sessions s ON r.session_id = s.id
                  WHERE s.speaker_id = ? AND s.status = 'completed'
              )
            ORDER BY p.id ASC
            LIMIT ?
            """,
            (category_id, speaker_id, limit)
        )
        rows = await cursor.fetchall()
        results = [dict(r) for r in rows]
        if not results:
            # Agar barcha matnlar o'qib bo'lingan bo'lsa, eng kam o'qilganlaridan beradi
            cur_fallback = await db.execute(
                "SELECT * FROM prompts WHERE category_id = ? AND is_active = 1 ORDER BY RANDOM() LIMIT ?",
                (category_id, limit)
            )
            results = [dict(r) for r in await cur_fallback.fetchall()]
        return results


# ==================== SESSIONS & RECORDINGS ====================

async def get_active_session(user_id: int):
    async with get_db() as db:
        cursor = await db.execute(
            """
            SELECT s.*, c.title as category_title, sp.name as speaker_name, sp.gender, sp.age
            FROM sessions s
            JOIN categories c ON s.category_id = c.id
            JOIN speakers sp ON s.speaker_id = sp.id
            WHERE s.user_id = ? AND s.status = 'in_progress'
            ORDER BY s.id DESC LIMIT 1
            """,
            (user_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def start_session(user_id: int, speaker_id: int, category_id: int, batch_size: int = 5):
    # Oldingi tugallanmagan sessiya bo'lsa uni bekor qilamiz
    async with get_db() as db:
        await db.execute(
            "UPDATE sessions SET status = 'cancelled' WHERE user_id = ? AND status = 'in_progress'",
            (user_id,)
        )
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = await db.execute(
            """
            INSERT INTO sessions (user_id, speaker_id, category_id, batch_size, status, created_at)
            VALUES (?, ?, ?, ?, 'in_progress', ?)
            """,
            (user_id, speaker_id, category_id, batch_size, now)
        )
        await db.commit()
        return cursor.lastrowid


async def add_recording(session_id: int, speaker_id: int, prompt_id: int, file_id: str, file_path: str, duration: float, file_size: int):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    async with get_db() as db:
        cursor = await db.execute(
            """
            INSERT INTO recordings (session_id, speaker_id, prompt_id, file_id, file_path, duration, file_size, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (session_id, speaker_id, prompt_id, file_id, file_path, duration, file_size, now)
        )
        await db.commit()
        return cursor.lastrowid


async def get_session_recordings_count(session_id: int):
    async with get_db() as db:
        cursor = await db.execute("SELECT COUNT(*) as cnt FROM recordings WHERE session_id = ?", (session_id,))
        row = await cursor.fetchone()
        return row["cnt"] if row else 0


async def complete_session(session_id: int):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    async with get_db() as db:
        await db.execute(
            "UPDATE sessions SET status = 'completed', completed_at = ? WHERE id = ?",
            (now, session_id)
        )
        await db.commit()


async def cancel_session(session_id: int):
    async with get_db() as db:
        await db.execute("UPDATE sessions SET status = 'cancelled' WHERE id = ?", (session_id,))
        await db.commit()


# ==================== STATS & EXPORT ====================

async def get_overall_stats():
    async with get_db() as db:
        # Userlar soni
        u_cur = await db.execute("SELECT COUNT(*) as cnt FROM users")
        total_users = (await u_cur.fetchone())["cnt"]

        # Spikerlar soni
        sp_cur = await db.execute("SELECT COUNT(*) as cnt FROM speakers")
        total_speakers = (await sp_cur.fetchone())["cnt"]

        # Jinslar taqsimoti
        g_cur = await db.execute("SELECT gender, COUNT(*) as cnt FROM speakers GROUP BY gender")
        gender_dist = {r["gender"]: r["cnt"] for r in await g_cur.fetchall()}

        # Tugallangan sessiyalar va jami ovozlar
        sess_cur = await db.execute(
            """
            SELECT COUNT(DISTINCT s.id) as completed_sessions,
                   COUNT(r.id) as total_recordings,
                   COALESCE(SUM(r.duration), 0) as total_duration
            FROM sessions s
            JOIN recordings r ON s.id = r.session_id
            WHERE s.status = 'completed'
            """
        )
        sess_data = await sess_cur.fetchone()

        # Toifalar bo'yicha taqsimot
        cat_cur = await db.execute(
            """
            SELECT c.title, COUNT(r.id) as cnt
            FROM recordings r
            JOIN sessions s ON r.session_id = s.id
            JOIN categories c ON s.category_id = c.id
            WHERE s.status = 'completed'
            GROUP BY c.id
            """
        )
        cat_dist = [dict(r) for r in await cat_cur.fetchall()]

        # Tugallanmagan (draft / bekor qilingan) sessiyalar
        draft_cur = await db.execute("SELECT COUNT(*) as cnt FROM sessions WHERE status != 'completed'")
        abandoned_sessions = (await draft_cur.fetchone())["cnt"]

        return {
            "total_users": total_users,
            "total_speakers": total_speakers,
            "gender_dist": gender_dist,
            "completed_sessions": sess_data["completed_sessions"],
            "total_recordings": sess_data["total_recordings"],
            "total_duration": round(sess_data["total_duration"], 1),
            "cat_dist": cat_dist,
            "abandoned_sessions": abandoned_sessions
        }


async def get_user_stats(user_id: int):
    async with get_db() as db:
        sp_cur = await db.execute("SELECT COUNT(*) as cnt FROM speakers WHERE user_id = ?", (user_id,))
        speakers_count = (await sp_cur.fetchone())["cnt"]

        sess_cur = await db.execute(
            """
            SELECT COUNT(DISTINCT s.id) as completed_sessions,
                   COUNT(r.id) as total_recordings,
                   COALESCE(SUM(r.duration), 0) as total_duration
            FROM sessions s
            JOIN recordings r ON s.id = r.session_id
            WHERE s.user_id = ? AND s.status = 'completed'
            """,
            (user_id,)
        )
        row = await sess_cur.fetchone()
        return {
            "speakers_count": speakers_count,
            "completed_sessions": row["completed_sessions"],
            "total_recordings": row["total_recordings"],
            "total_duration": round(row["total_duration"], 1)
        }


async def get_speakers_by_filter(gender: str = None, min_age: int = None, max_age: int = None):
    """Admin uchun spikerlarni jins va yosh guruhlari bo'yicha filtrlash"""
    query = """
        SELECT s.*, u.username, u.first_name as user_first_name,
               COUNT(DISTINCT r.id) as recordings_count,
               COUNT(DISTINCT sess.id) as completed_sessions
        FROM speakers s
        JOIN users u ON s.user_id = u.user_id
        LEFT JOIN recordings r ON s.id = r.speaker_id
        LEFT JOIN sessions sess ON r.session_id = sess.id AND sess.status = 'completed'
        WHERE 1=1
    """
    params = []
    if gender:
        query += " AND s.gender = ?"
        params.append(gender)
    if min_age is not None:
        query += " AND s.age >= ?"
        params.append(min_age)
    if max_age is not None:
        query += " AND s.age <= ?"
        params.append(max_age)

    query += " GROUP BY s.id ORDER BY s.id DESC"
    async with get_db() as db:
        cursor = await db.execute(query, tuple(params))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_export_dataset_rows(category_id: int = None, user_id: int = None, speaker_id: int = None):
    """
    Faqat status='completed' bo'lgan sessiyalardagi ovozlarni qaytaradi.
    Filtrlar: category_id, user_id, speaker_id bo'yicha moslashuvchan.
    """
    query = """
        SELECT r.id as recording_id,
               r.file_path,
               r.duration,
               r.file_size,
               r.created_at,
               p.text as prompt_text,
               c.id as category_id,
               c.code as category_code,
               c.title as category_title,
               sp.id as speaker_id,
               sp.name as speaker_name,
               sp.gender as speaker_gender,
               sp.age as speaker_age,
               s.user_id as telegram_user_id,
               s.id as session_id
        FROM recordings r
        JOIN sessions s ON r.session_id = s.id
        JOIN prompts p ON r.prompt_id = p.id
        JOIN categories c ON s.category_id = c.id
        JOIN speakers sp ON r.speaker_id = sp.id
        WHERE s.status = 'completed'
    """
    params = []
    if category_id:
        query += " AND c.id = ?"
        params.append(category_id)
    if user_id:
        query += " AND s.user_id = ?"
        params.append(user_id)
    if speaker_id:
        query += " AND sp.id = ?"
        params.append(speaker_id)

    query += " ORDER BY r.id ASC"

    async with get_db() as db:
        cursor = await db.execute(query, tuple(params))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_all_speakers():
    """Barcha spikerlarni ro'yxatini to'liq parametrlar bilan qaytaradi"""
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM speakers ORDER BY id ASC")
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_speech_commands_export_data():
    """
    Google Speech Commands standarti (uz_robot_cmd):
    - Har bir diktor uchun ID: spk001, spk002...
    - speakers.csv: speaker_id, jins, yosh_guruhi, hudud, qurilma, muhit
    - splits.csv: audio_path, speaker_id, command, split
    - 80% train, 10% val, 10% test (har bir diktor faqat bitta guruhda)
    - Fayl nomi: spk001_oldinga_01.wav
    """
    import re
    import hashlib

    # 1. Spikerlarni olish
    speakers = await get_all_speakers()
    speaker_map = {}
    for idx, sp in enumerate(speakers):
        spk_tag = f"spk{sp['id']:03d}"
        
        # Jinsni o'zbekchaga moslash
        g_raw = (sp.get("gender") or "male").lower()
        jins = "ayol" if g_raw in ("female", "ayol") else "erkak"
        
        # Yosh guruhi
        age = sp.get("age", 20)
        age_grp = sp.get("age_group") or compute_age_group(age)
        
        hudud = sp.get("region") or "Toshkent"
        qurilma = sp.get("device") or "smartfon"

        # 80% train, 10% val, 10% test (speaker-disjoint split)
        # Deterministik va adolatli taqsimlash
        h = int(hashlib.md5(f"split_{spk_tag}".encode()).hexdigest(), 16) % 100
        if len(speakers) == 1:
            split_grp = "train"
        elif len(speakers) == 2:
            split_grp = "train" if idx == 0 else "test"
        elif len(speakers) == 3:
            split_grp = ["train", "val", "test"][idx]
        else:
            if h < 80:
                split_grp = "train"
            elif h < 90:
                split_grp = "val"
            else:
                split_grp = "test"

        speaker_map[sp["id"]] = {
            "speaker_id": spk_tag,
            "raw_id": sp["id"],
            "name": sp.get("name"),
            "jins": jins,
            "yosh_guruhi": age_grp,
            "hudud": hudud,
            "qurilma": qurilma,
            "split": split_grp
        }

    # 2. Barcha yozuvlarni olish (kamida 1 ta ovoz yozilganlar)
    query = """
        SELECT r.id as recording_id,
               r.file_path,
               r.duration,
               r.file_size,
               r.created_at,
               p.text as prompt_text,
               c.code as category_code,
               c.title as category_title,
               r.speaker_id,
               s.status as session_status
        FROM recordings r
        JOIN prompts p ON r.prompt_id = p.id
        JOIN sessions s ON r.session_id = s.id
        JOIN categories c ON s.category_id = c.id
        ORDER BY r.speaker_id ASC, p.id ASC, r.id ASC
    """
    async with get_db() as db:
        cursor = await db.execute(query)
        recordings = [dict(r) for r in await cursor.fetchall()]

    # 3. Buyruq va takrorlarni hisoblash (Faqat 20 ta robot buyruqlari)
    repeat_tracker = {} # (spk_tag, folder_name) -> count
    export_items = []

    # 20 ta standart robot buyruqlari xaritasi (O'zbekcha buyruq -> Sinf nomi va papka)
    ROBOT_COMMANDS_MAP = {
        "oldinga yur": {"class": "FORWARD", "folder": "forward"},
        "oldinga": {"class": "FORWARD", "folder": "forward"},
        "orqaga yur": {"class": "BACKWARD", "folder": "backward"},
        "orqaga": {"class": "BACKWARD", "folder": "backward"},
        "chapga buril": {"class": "LEFT", "folder": "left"},
        "chapga": {"class": "LEFT", "folder": "left"},
        "o'ngga buril": {"class": "RIGHT", "folder": "right"},
        "o'ngga": {"class": "RIGHT", "folder": "right"},
        "to'xta": {"class": "STOP", "folder": "stop"},
        "davom et": {"class": "RESUME", "folder": "resume"},
        "boshlash": {"class": "START", "folder": "start"},
        "boshla": {"class": "START", "folder": "start"},
        "tezroq yur": {"class": "SPEED_UP", "folder": "speed_up"},
        "tezroq": {"class": "SPEED_UP", "folder": "speed_up"},
        "sekinroq yur": {"class": "SLOW_DOWN", "folder": "slow_down"},
        "sekinroq": {"class": "SLOW_DOWN", "folder": "slow_down"},
        "chapga burilma": {"class": "NO_LEFT", "folder": "no_left"},
        "o'ngga burilma": {"class": "NO_RIGHT", "folder": "no_right"},
        "to'siqni aylanib o't": {"class": "AVOID", "folder": "avoid"},
        "orqaga qayt": {"class": "RETURN", "folder": "return"},
        "uyga qayt": {"class": "GO_HOME", "folder": "go_home"},
        "qo'lni ko'tar": {"class": "ARM_UP", "folder": "arm_up"},
        "qo'lni tushir": {"class": "ARM_DOWN", "folder": "arm_down"},
        "ushla": {"class": "GRAB", "folder": "grab"},
        "qo'yib yubor": {"class": "RELEASE", "folder": "release"},
        "holatingni ko'rsat": {"class": "STATUS", "folder": "status"},
        "takrorla": {"class": "REPEAT", "folder": "repeat"},
        "yoq": {"class": "START", "folder": "start"},
        "o'chir": {"class": "STOP", "folder": "stop"}
    }

    for r in recordings:
        spk_info = speaker_map.get(r["speaker_id"])
        if not spk_info:
            continue

        raw_text = r["prompt_text"].strip()
        prompt_clean = raw_text.lower()
        prompt_clean = re.sub(r"[^\w\s']", "", prompt_clean).strip()

        # Buyruq papkasi va sinf nomini aniqlash (faqat 20 ta buyruq)
        matched_info = None
        if prompt_clean in ROBOT_COMMANDS_MAP:
            matched_info = ROBOT_COMMANDS_MAP[prompt_clean]
        else:
            for k, val in ROBOT_COMMANDS_MAP.items():
                if k in prompt_clean:
                    matched_info = val
                    break

        # Begona so'zlar va background chiqarib tashlanadi, faqat 20 ta buyruq qoladi
        if not matched_info:
            continue

        folder_name = matched_info["folder"]
        class_name = matched_info["class"]
        cmd_slug = matched_info["folder"]

        spk_tag = spk_info["speaker_id"]
        key = (spk_tag, folder_name)
        repeat_tracker[key] = repeat_tracker.get(key, 0) + 1
        repeat_idx = repeat_tracker[key]

        # Standart fayl nomi: diktorID_buyruq_takror.wav
        filename = f"{spk_tag}_{cmd_slug}_{repeat_idx:02d}.wav"
        rel_path = f"{folder_name}/{filename}"

        export_items.append({
            "original_file_path": r["file_path"],
            "folder_name": folder_name,
            "class_name": class_name,
            "filename": filename,
            "archive_path": f"uz_robot_cmd/{rel_path}",
            "rel_path": rel_path,
            "speaker_id": spk_tag,
            "command": raw_text,
            "repeat": repeat_idx,
            "split": spk_info["split"],
            "prompt_text": raw_text,
            "duration": r["duration"]
        })

    return {
        "speakers": list(speaker_map.values()),
        "items": export_items
    }

