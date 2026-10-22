import asyncio
import logging
import wave
import array
import math
from pathlib import Path

logger = logging.getLogger(__name__)


def get_exact_wav_duration(wav_path: Path) -> float:
    """WAV faylning haqiqiy davomiyligini millisekund aniqlikda qaytaradi"""
    try:
        with wave.open(str(wav_path), "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            if rate > 0:
                return round(frames / float(rate), 3)
    except Exception as e:
        logger.warning(f"WAV davomiyligini hisoblashda xato: {e}")
    return 0.0


def center_and_pad_to_1sec(input_wav: Path, output_wav: Path = None, target_samples: int = 16000) -> bool:
    """
    Google Speech Commands standarti:
    Audio uzunligini roppa-rosa 1.0 soniya (16000 sample, 16-bit mono) qiladi.
    Nutq qismini (Voice Activity) aniqlab, buyruqni audio markaziga joylashtiradi,
    oldi va ortida tabiiy jimlik (silence padding) qoldiradi.
    """
    if output_wav is None:
        output_wav = input_wav

    try:
        with wave.open(str(input_wav), "rb") as wf:
            framerate = wf.getframerate()
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            n_frames = wf.getnframes()
            raw_bytes = wf.readframes(n_frames)

        samples = array.array("h", raw_bytes)
        total_len = len(samples)
        if total_len == 0:
            return False

        # 10ms darchalar bo'yicha energiya hisoblash (160 sample)
        win_size = max(1, int(framerate * 0.01))
        energies = []
        for i in range(0, total_len, win_size):
            chunk = samples[i:i + win_size]
            if not chunk:
                continue
            energy = math.sqrt(sum(s * s for s in chunk) / len(chunk))
            energies.append((i, i + len(chunk), energy))

        if not energies:
            speech_start, speech_end = 0, total_len
        else:
            max_energy = max(e[2] for e in energies) if energies else 1
            threshold = max(max_energy * 0.15, 300)
            active_windows = [e for e in energies if e[2] >= threshold]
            if active_windows:
                speech_start = active_windows[0][0]
                speech_end = active_windows[-1][1]
            else:
                speech_start, speech_end = 0, total_len

        # Nutqning markaziy nuqtasi
        speech_center = (speech_start + speech_end) // 2

        # 16000 samplelik darchaning boshlanishi va tugashi
        desired_start = speech_center - (target_samples // 2)
        desired_end = desired_start + target_samples

        out_samples = array.array("h", [0] * target_samples)
        src_start = max(0, desired_start)
        src_end = min(total_len, desired_end)

        if src_start < src_end:
            dst_start = src_start - desired_start
            dst_end = dst_start + (src_end - src_start)
            out_samples[dst_start:dst_end] = samples[src_start:src_end]

        with wave.open(str(output_wav), "wb") as out_wf:
            out_wf.setnchannels(1)
            out_wf.setsampwidth(2)  # 16-bit
            out_wf.setframerate(target_samples)  # 16000 Hz
            out_wf.writeframes(out_samples.tobytes())

        return True
    except Exception as e:
        logger.error(f"1 soniyaga keltirishda xatolik: {e}")
        return False


async def convert_ogg_to_wav(
    ogg_path: Path,
    wav_path: Path,
    sample_rate: int = 16000,
    remove_ogg: bool = True,
    make_1sec_centered: bool = False
) -> bool:
    """
    Telegram .ogg (Opus) faylini 16kHz mono 16-bit .wav formatiga o'tkazadi.
    Agar make_1sec_centered=True bo'lsa, Google Speech Commands talabiga ko'ra
    buyruqni o'rtaga qo'yib, aniq 1 soniya (16000 samples) qilib kesadi/pad qiladi.
    """
    try:
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg",
            "-y",
            "-i", str(ogg_path),
            "-ar", str(sample_rate),
            "-ac", "1",
            "-c:a", "pcm_s16le",
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

            # Agar 1 soniyalik Speech Commands formati so'ralsa
            if make_1sec_centered:
                center_and_pad_to_1sec(wav_path, wav_path, target_samples=sample_rate)

            return True
        else:
            logger.error(f"FFmpeg xatosi: {stderr.decode('utf-8', errors='ignore')}")
            return False
    except Exception as e:
        logger.error(f"Audio konvertatsiyada xatolik: {e}")
        return False
