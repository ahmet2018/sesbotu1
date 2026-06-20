# Discord Müzik Botu (Render Uyumlu)

Bu bot, Render üzerinde 7/24 çalışacak şekilde tasarlanmıştır. Flask web sunucusu sayesinde Render botun uyumasını engeller.

## Özellikler
- `n!join <kanal_id>`: Belirtilen ses kanalına katılır.
- `n!play <şarkı_adı_veya_url>`: Şarkı çalar.
- `n!stop`: Ses kanalından ayrılır.
- **Flask Entegrasyonu**: Sitede "Bot Aktif!" yazısı görünür.

## Kurulum
1. Discord Developer Portal'dan bir bot oluşturun ve tokenını alın.
2. `Privileged Gateway Intents` kısmından **Message Content Intent**'i aktif edin.
3. Botu sunucunuza `Administrator` yetkisiyle davet edin.
4. Render.com üzerinde yeni bir **Web Service** oluşturun.
5. Environment Variables kısmına `DISCORD_TOKEN` anahtarını ve tokenınızı ekleyin.

## Render Ayarları
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python main.py`
