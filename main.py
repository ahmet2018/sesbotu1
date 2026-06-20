import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio
from flask import Flask
from threading import Thread
import os

# 1. FLASK SUNUCUSU (Render'da 7/24 Aktif Kalmak İçin)
app = Flask('')
@app.route('/')
def home(): return "<h1>Bot Aktif!</h1><p>Jockie Music Tarzi Altyapi Calisiyor.</p>"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# 2. BOT SINIFI VE SLASH KOMUT AYARLARI
class JockieStyleBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print(f"Slash komutlari senkronize edildi!")

bot = JockieStyleBot()

# 3. YOUTUBE ENGEL ASICI (Jockie Music Mantigi)
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
    # YouTube Engelini Asmak Icin Guncel Headerlar
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'referer': 'https://www.google.com/',
}

ffmpeg_options = {
    'options': '-vn',
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options )

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.thumbnail = data.get('thumbnail')
        self.duration = data.get('duration')
        self.url = data.get('webpage_url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data: data = data['entries'][0]
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

# 4. JOCKIE MUSIC TARZI PROFESYONEL KOMUTLAR
@bot.tree.command(name="join", description="Ses kanalina katilir ve sagirlasir")
async def join(interaction: discord.Interaction, kanal_id: str):
    try:
        channel = bot.get_channel(int(kanal_id))
        if not channel: return await interaction.response.send_message("❌ Kanal ID hatali!", ephemeral=True)
        
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.move_to(channel)
        else:
            await channel.connect(self_deaf=True) # Otomatik sagirlastirma
        
        embed = discord.Embed(title="📥 Kanala Katildi", description=f"**{channel.name}** kanalina giris yaptim.", color=0x2f3136)
        embed.set_footer(text="Jockie Music Altyapisi")
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)

@bot.tree.command(name="play", description="Muzik calar (Jockie Music Tarzi)")
async def play(interaction: discord.Interaction, sarki: str):
    if not interaction.guild.voice_client:
        return await interaction.response.send_message("❌ Önce `/join` yapmalisin!", ephemeral=True)

    await interaction.response.defer()
    try:
        player = await YTDLSource.from_url(sarki, loop=bot.loop, stream=True)
        interaction.guild.voice_client.play(player)
        
        # Jockie Music Tarzi Zengin Embed Mesaji
        embed = discord.Embed(title="🎶 Simdi Caliyor", description=f"[{player.title}]({player.url})", color=0x5865f2)
        if player.thumbnail: embed.set_thumbnail(url=player.thumbnail)
        embed.add_field(name="Süre", value=f"{player.duration // 60}:{player.duration % 60:02d}", inline=True)
        embed.add_field(name="Talep Eden", value=interaction.user.mention, inline=True)
        embed.set_footer(text="Jockie Music Altyapisi | 7/24 Aktif")
        
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ YouTube Hatasi: {e}\n*YouTube bazen sunucuyu engeller, baska sarki deneyin.*")

@bot.tree.command(name="stop", description="Muzigi durdurur ve ayrilir")
async def stop(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("👋 Muzik durduruldu ve kanaldan ayrildim.")
    else:
        await interaction.response.send_message("Zaten bir kanalda degilim.", ephemeral=True)

if __name__ == "__main__":
    keep_alive()
    token = os.getenv('DISCORD_TOKEN')
    bot.run(token)
