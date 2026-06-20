import discord
from discord.ext import commands
from discord import app_commands
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
class MusicBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        # Slash komutları için Message Content Intent'e gerek kalmadı ama default kalsın
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self):
        # Slash komutlarını senkronize et
        await self.tree.sync()
        print(f"Slash komutları senkronize edildi!")

bot = MusicBot()

# yt-dlp ve FFmpeg Ayarları
ytdl_format_options = {
    'format': 'bestaudio/best',
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
    print(f'{bot.user.name} olarak giriş yapıldı ve Slash komutları hazır!')

# SLASH KOMUTLARI
@bot.tree.command(name="join", description="Ses kanalına ID ile katılır")
async def join(interaction: discord.Interaction, kanal_id: str):
    try:
        channel = bot.get_channel(int(kanal_id))
        if not channel:
            return await interaction.response.send_message("❌ Hata: Geçersiz kanal ID'si!", ephemeral=True)
        
        if interaction.guild.voice_client is not None:
            await interaction.guild.voice_client.move_to(channel)
        else:
            await channel.connect()
        await interaction.response.send_message(f"✅ **{channel.name}** kanalına başarıyla katıldım!")
    except Exception as e:
        await interaction.response.send_message(f"❌ Bir hata oluştu: {str(e)}", ephemeral=True)

@bot.tree.command(name="play", description="Müzik çalar (Link veya isim)")
async def play(interaction: discord.Interaction, sarki: str):
    if interaction.guild.voice_client is None:
        return await interaction.response.send_message("❌ Önce botu bir kanala sokmalısın! `/join` komutunu kullan.", ephemeral=True)

    await interaction.response.defer() # İşlem uzun sürebileceği için Discord'a 'bekle' diyoruz

    try:
        player = await YTDLSource.from_url(sarki, loop=bot.loop, stream=True)
        interaction.guild.voice_client.play(player, after=lambda e: print(f'Hata: {e}') if e else None)
        await interaction.followup.send(f'🎵 Şimdi çalıyor: **{player.title}**')
    except Exception as e:
        await interaction.followup.send(f"❌ Müzik çalınırken hata oluştu: {str(e)}")

@bot.tree.command(name="stop", description="Botu kanaldan çıkarır")
async def stop(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("👋 Görüşürüz, kanaldan ayrıldım!")
    else:
        await interaction.response.send_message("Zaten bir kanalda değilim.", ephemeral=True)

if __name__ == "__main__":
    keep_alive()
    token = os.getenv('DISCORD_TOKEN')
    if token:
        bot.run(token)
    else:
        print("Hata: DISCORD_TOKEN bulunamadı! Render üzerinden Environment Variables kısmına ekle.")
