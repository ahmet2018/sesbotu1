import discord
from discord.ext import commands
import yt_dlp
import asyncio
from flask import Flask
from threading import Thread
import os

# Flask Sunucusu (Render'da botun aktif kalmasını sağlar)
app = Flask('')

@app.route('/')
def home():
    return "Bot Aktif!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Discord Bot Ayarları
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='n!', intents=intents)

# yt-dlp Ayarları
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ffmpeg_options = {
    'options': '-vn',
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

@bot.event
async def on_ready():
    print(f'{bot.user.name} olarak giriş yapıldı!')

@bot.command(name='join')
async def join(ctx, channel_id: int):
    channel = bot.get_channel(channel_id)
    if not channel:
        return await ctx.send("Geçersiz kanal ID'si!")
    
    if ctx.voice_client is not None:
        return await ctx.voice_client.move_to(channel)

    await channel.connect()
    await ctx.send(f"{channel.name} kanalına katıldım!")

@bot.command(name='play')
async def play(ctx, *, url):
    if ctx.voice_client is None:
        return await ctx.send("Önce botu bir ses kanalına sokmalısın (n!join <id>)")

    async with ctx.typing():
        player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
        ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)

    await ctx.send(f'Şimdi çalıyor: {player.title}')

@bot.command(name='stop')
async def stop(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Ses kanalından ayrıldım.")

if __name__ == "__main__":
    keep_alive()
    token = os.getenv('DISCORD_TOKEN')
    if token:
        bot.run(token)
    else:
        print("Hata: DISCORD_TOKEN bulunamadı!")
