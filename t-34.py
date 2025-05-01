import discord
from discord.ext import tasks, commands
import yt_dlp
import asyncio
import datetime
import pytz

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

GUILD_ID = 1225075859333845154     # ID сервера
VOICE_CHANNEL_ID = 1289694911234310155  # Канал "Москва"
TEXT_CHANNEL_ID = 1225075859799670918   # Главный текстовый канал
YOUTUBE_URL = "https://www.youtube.com/watch?v=H7p7v9aHYxs"  # Вставь сам
GREETING_IMAGE_PATH = "card.jpg"
GREETING_IMAGE_PATH2 = "card2.jpg" # Вставь сам

sent_dm_users = set()
has_sent_main_greeting = False

moscow_tz = pytz.timezone("Europe/Moscow")

@bot.event
async def on_ready():
    print(f"Запущен как {bot.user}")
    check_time.start()
    reconnect_loop.start()

@tasks.loop(minutes=1)
async def check_time():
    global has_sent_main_greeting

    now = datetime.datetime.now(tz=moscow_tz)

    # Проверка на 9 мая
    if now.month == 5 and now.day == 9:
        # 00:00 — поздравление в текстовый канал
        if now.hour == 00 and now.minute == 00 and not has_sent_main_greeting:
            channel = bot.get_channel(TEXT_CHANNEL_ID)
            if channel:
                await channel.send("С Днём Победы! Помним, чтим, гордимся!", file=discord.File(GREETING_IMAGE_PATH2))
                has_sent_main_greeting = True

        # каждый час — музыка
        if now.minute == 0:
            voice_channel = bot.get_channel(VOICE_CHANNEL_ID)
            if voice_channel and isinstance(voice_channel, discord.VoiceChannel):
                vc = discord.utils.get(bot.voice_clients, guild=voice_channel.guild)
                if not vc or not vc.is_connected():
                    vc = await voice_channel.connect()
                elif vc.channel.id != VOICE_CHANNEL_ID:
                    await vc.move_to(voice_channel)

                # Остановить текущую музыку
                if vc.is_playing():
                    vc.stop()

                # Воспроизведение мелодии с YouTube
                ydl_opts = {'format': 'bestaudio'}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(YOUTUBE_URL, download=False)
                    url2 = info['url']
                    vc.play(discord.FFmpegPCMAudio(url2), after=lambda e: print("Завершено:", e))

@tasks.loop(seconds=10)
async def reconnect_loop():
    """Возврат в голосовой канал, если бот был отключён или перемещён"""
    voice_channel = bot.get_channel(VOICE_CHANNEL_ID)
    if not voice_channel:
        return

    vc = discord.utils.get(bot.voice_clients, guild=voice_channel.guild)
    if not vc or not vc.is_connected() or vc.channel.id != VOICE_CHANNEL_ID:
        try:
            if vc:
                await vc.disconnect(force=True)
            await voice_channel.connect()
        except:
            pass  # возможно, канал недоступен временно

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return

    now = datetime.datetime.now(tz=moscow_tz)
    if now.month == 5 and now.day == 9:
        # Пользователь впервые за день зашёл в "Москву"
        if after.channel and after.channel.id == VOICE_CHANNEL_ID:
            if member.id not in sent_dm_users:
                sent_dm_users.add(member.id)
                try:
                    await member.send("🎉 С Днём Победы! Спасибо за память!", file=discord.File(GREETING_IMAGE_PATH))
                except:
                    print(f"Не удалось отправить ЛС {member.name}")

bot.run("")
