import asyncio
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


async def convert_ogg_to_wav(ogg_path: Path, wav_path: Path, sample_rate: int = 16000, remove_ogg: bool = True) -> bool:
    """
    Telegram .ogg faylini 16kHz mono standart .wav formatiga o'tkazadi.
    Speech-to-Text va audio AI modellari uchun eng maqbul standart.
    """
    try:
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg",
            "-y",
            "-i", str(ogg_path),
            "-ar", str(sample_rate),
            "-ac", "1",
            str(wav_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode == 0:
            if remove_ogg and ogg_path.exists():
                try:
                    ogg_path.unlink()
                except Exception as e:
                    logger.warning(f"Ogg faylni o'chirishda ogohlantirish: {e}")
            return True
        else:
            logger.error(f"FFmpeg xatosi: {stderr.decode('utf-8', errors='ignore')}")
            return False
    except Exception as e:
        logger.error(f"Audio konvertatsiyada xatolik: {e}")
        return False
