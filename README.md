# 🚀 All Link Download Bot

A powerful, premium **Telegram bot** for downloading media from multiple platforms and converting between formats.

## ✨ Features

- **📥 Download** from: Dailymotion, Vimeo, VK, TikTok, Reddit, Threads, Xiaohongshu & more
- **🔄 Convert** between: MP3, MP4, MOV, GIF, MKV, WEBM
- **🎨 Premium VIP-style UI** with emoji-rich inline buttons
- **⚡ Fast processing** using yt-dlp + FFmpeg

## 🛠️ Tech Stack

- **Python 3.10+**
- **python-telegram-bot v21** (async)
- **yt-dlp** (media downloading)
- **FFmpeg** (media conversion)

## 🚀 Deploy on Render

### Prerequisites

1. A **Telegram Bot Token** from [@BotFather](https://t.me/BotFather)
2. A **GitHub** account connected to [Render](https://render.com)
3. **FFmpeg** installed on the Render instance (select the **Python + FFmpeg** environment or add a buildpack)

### Steps

1. **Fork / clone** this repository to your GitHub
2. **Create a new Worker** on Render:
   - Connect your GitHub repo
   - Set **Build Command**: `pip install -r requirements.txt`
   - Set **Start Command**: `python main.py`
3. **Add Environment Variable:**
   - `BOT_TOKEN` = your bot token from BotFather
   - `OWNER_USERNAME` = `raj169k`
   - `MODE` = `polling`
4. **Deploy!** 🎉

### ⚠️ FFmpeg on Render

Render's Python environment doesn't include FFmpeg by default.  
Add a **pre-build command** in Render's settings:

```bash
apt-get update && apt-get install -y ffmpeg
