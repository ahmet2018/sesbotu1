import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio
from flask import Flask
from threading import Thread
import os

# 1. FLASK SUNUCUSU (Render'da botun uyumasını engeller)
app = Flask('')

@app.route('/')
def home():
    return "Bot Aktif!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# 2. BOT SINIFI VE AYARLARI
class MusicBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True # Her ihtimale karşı açık kalsın
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self):
        # Slash komutlarını Discord'a bildirir
        await self.tree.sync()
        print("Slash komutları senkronize edildi!")

bot = MusicBot()

# 3. YOUTUBE VE SES AYARLARI
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
    'source_address': '0.0.0.0',
    # YouTube Engelini Aşmak İçin:
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
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

# 4. SLASH KOMUTLARI
@bot.tree.command(name="join", description="Ses kanalına ID ile katılır ve kendini sağırlaştırır")
async def join(interaction: discord.Interaction, kanal_id: str):
    try:
        channel = bot.get_channel(int(kanal_id))
        if not channel:
            return await interaction.response.send_message("❌ Hata: Geçersiz kanal ID'si!", ephemeral=True)
        
        # self_deaf=True ile bot kendini sağırlaştırır
        if interaction.guild.voice_client is not None:
            await interaction.guild.voice_client.move_to(channel)
        else:
            await channel.connect(self_deaf=True)
        
        await interaction.response.send_message(f"✅ **{channel.name}** kanalına katıldım ve sağırlaştım!")
    except Exception as e:
        await interaction.response.send_message(f"❌ Hata: {str(e)}", ephemeral=True)

@bot.tree.command(name="play", description="Müzik çalar (Link veya isim)")
async def play(interaction: discord.Interaction, sarki: str):
    if interaction.guild.voice_client is None:
        return await interaction.response.send_message("❌ Önce botu kanala sok! (/join)", ephemeral=True)

    await interaction.response.defer()

    try:
        player = await YTDLSource.from_url(sarki, loop=bot.loop, stream=True)
        interaction.guild.voice_client.play(player)
        await interaction.followup.send(f'🎵 Şimdi çalıyor: **{player.title}**')
    except Exception as e:
        await interaction.followup.send(f"❌ Hata: {str(e)}")

@bot.tree.command(name="stop", description="Kanaldan ayrılır")
async def stop(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("👋 Kanaldan ayrıldım!")
    else:
        await interaction.response.send_message("Zaten bir kanalda değilim.", ephemeral=True)

# 5. BOTU ÇALIŞTIR
if __name__ == "__main__":
    keep_alive()
    token = os.getenv('DISCORD_TOKEN')
    if token:
        bot.run(token)
    else:
        print("Hata: DISCORD_TOKEN bulunamadı!")
