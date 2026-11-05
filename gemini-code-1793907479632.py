import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile
import yt_dlp

TOKEN = "9092644188:AAFoQpvEawkuRw6RzGsZWz91IVspDSP9av8"
ADMIN_ID = 6887395659

if not os.path.exists("downloads"):
    os.makedirs("downloads")

bot = Bot(token=TOKEN)
dp = Dispatcher()

def download_audio(query_or_url: str):
    """Завантажує найкраще доступне аудіо без потреби у FFmpeg"""
    if not query_or_url.startswith("http"):
        search_target = f"ytsearch1:{query_or_url}"
    else:
        search_target = query_or_url

    ydl_opts = {
        'format': 'bestaudio',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'quiet': True,
        'noplaylist': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_target, download=True)
            if 'entries' in info:
                info = info['entries'][0]
            
            filename = ydl.prepare_filename(info)
            title = info.get('title', 'Повна пісня')
            uploader = info.get('uploader', 'Невідомий виконавець')
            return filename, title, uploader
    except Exception as e:
        print(f"Помилка завантаження: {e}")
        return None, None, None

@dp.message(Command("start"))
async def cmd_start(message: Message):
    if message.from_user.id == ADMIN_ID:
        text = "Привіт, господарю! 👑 Бот готовий качати треки.\n\nКидай посилання (TikTok, YouTube тощо) або назву пісні!"
    else:
        text = "Привіт! Напиши назву пісні або кидай посилання."
    await message.answer(text)

@dp.message(F.text)
async def handle_song_request(message: Message):
    query = message.text.strip()
    
    waiting_msg = await message.answer("🔍 Шукаю і завантажую трек, зачекай...")

    loop = asyncio.get_running_loop()
    file_path, title, uploader = await loop.run_in_executor(None, download_audio, query)

    if not file_path or not os.path.exists(file_path):
        await waiting_msg.edit_text("😔 Не вдалося знайти або завантажити трек. Спробуй інше посилання чи назву.")
        return

    await waiting_msg.edit_text("📤 Надсилаю аудіо...")

    try:
        audio_file = FSInputFile(file_path)
        await message.answer_audio(
            audio=audio_file,
            title=title,
            performer=uploader,
            caption=f"🎵 **{title}**\n👤 {uploader}"
        )
        await waiting_msg.delete()
    except Exception as e:
        logging.error(f"Помилка надсилання: {e}")
        await waiting_msg.edit_text("⚠️ Сталася помилка при надсиланні файлу.")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

async def main():
    logging.basicConfig(level=logging.INFO)
    print("Бот успішно запущено!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())