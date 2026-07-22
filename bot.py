import re
import os
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

from config import config
from downloader import detect_platform, download_media, get_file_size as dl_size, clean_up as dl_clean
from converter import convert_media, get_file_size as conv_size, clean_up as conv_clean


# ════════════════════════════════════════════════════════════════════════
#  KEYBOARD BUILDERS
# ════════════════════════════════════════════════════════════════════════

def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Two-row layout: platform buttons + convert buttons."""
    kb = []

    # Row 1 — Platform buttons (3 per row)
    platforms = list(config.PLATFORMS.items())
    for i in range(0, len(platforms), 3):
        row = []
        for key, val in platforms[i:i + 3]:
            row.append(InlineKeyboardButton(val["label"], callback_data=f"platform:{key}"))
        kb.append(row)

    # Row 2 — Conversion buttons (2 per row)
    convs = list(config.CONVERSIONS.items())
    for i in range(0, len(convs), 2):
        row = []
        for key, val in convs[i:i + 2]:
            row.append(InlineKeyboardButton(val["label"], callback_data=f"convert:{key}"))
        kb.append(row)

    # Footer
    kb.append([InlineKeyboardButton("❓ Help", callback_data="help"),
               InlineKeyboardButton("ℹ️ About", callback_data="about")])

    return InlineKeyboardMarkup(kb)


def platform_keyboard(platform_key: str) -> InlineKeyboardMarkup:
    """Show platform info + back button."""
    info = config.PLATFORMS.get(platform_key, {"label": platform_key})
    kb = [
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_menu")],
        [InlineKeyboardButton("📤 Send a link now", callback_data="send_link")],
    ]
    return InlineKeyboardMarkup(kb)


# ════════════════════════════════════════════════════════════════════════
#  HANDLERS
# ════════════════════════════════════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Premium welcome message."""
    first_name = update.effective_user.first_name or "there"
    welcome_text = f"""
🚀 **All Link Download Bot** — *Premium Edition*

━━━━━━━━━━━━━━━━━━━━━━━

🌟 Welcome, **{first_name}**!  
You've activated the most powerful **all-in-one media downloader & converter** on Telegram.

👑 **Owner:** @{config.OWNER_USERNAME}

━━━━━━━━━━━━━━━━━━━━━━━

**📥 How to Use —**

Simply **send me any link** from the supported platforms below, and I'll download it instantly!  

Or use the inline buttons to:
• Choose a platform 📱  
• Convert media between formats 🎞️  
• Get help & info ❓

━━━━━━━━━━━━━━━━━━━━━━━

**✅ Supported Platforms:**

📺 Dailymotion  |  🎬 Vimeo  |  🌐 VK  
🎵 TikTok  |  👽 Reddit  |  🧵 Threads  |  📕 Xiaohongshu

**🔄 Media Converter:**

🎵 MP3  |  🎥 MP4  |  🎞️ MOV  |  🎨 GIF  |  📦 MKV  
› Plus cross-format conversions!

━━━━━━━━━━━━━━━━━━━━━━━

*⚡ Just paste a link or tap a button below to begin!*
"""

    await update.message.reply_text(
        welcome_text,
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Help text."""
    text = f"""
❓ **All Link Download Bot — Help**

━━━━━━━━━━━━━━━━━━━━━━━

**📌 How to download:**

1️⃣ Copy a link from a supported platform  
2️⃣ Paste it here in the chat  
3️⃣ Wait while I process & download it  
4️⃣ Receive your media file! 🎉

━━━━━━━━━━━━━━━━━━━━━━━

**🔄 How to convert:**

1️⃣ Send me a media file (or use a downloaded one)  
2️⃣ Tap the conversion button you need  
3️⃣ I'll convert & send it back

━━━━━━━━━━━━━━━━━━━━━━━

**📋 Supported platforms:**  
Dailymotion, Vimeo, VK, TikTok, Reddit, Threads, Xiaohongshu + many more via direct link!

**🎯 Supported conversions:**  
MP3, MP4, MOV, GIF, MKV, WEBM & cross-format.

━━━━━━━━━━━━━━━━━━━━━━━

👑 **Owner:** @{config.OWNER_USERNAME}  
⚡ **Bot:** All Link Download Bot
"""
    await update.message.reply_text(text, parse_mode="Markdown")
    await update.message.reply_text("🔙 Tap below to return:", reply_markup=main_menu_keyboard())


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """About the bot."""
    text = f"""
ℹ️ **About All Link Download Bot**

━━━━━━━━━━━━━━━━━━━━━━━

🚀 **Version:** 2.0 Premium  
👑 **Developer:** @{config.OWNER_USERNAME}  
🤖 **Bot:** All Link Download Bot

**Capabilities:**
• Download media from 7+ platforms  
• Convert between 10+ media formats  
• High-speed processing  
• Premium UI & experience

━━━━━━━━━━━━━━━━━━━━━━━

*Built with ❤️ for the Telegram community.*
"""
    await update.message.reply_text(text, parse_mode="Markdown")
    await update.message.reply_text("🔙 Back to menu:", reply_markup=main_menu_keyboard())


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle incoming text messages — treat as a download link.
    Also handles media files (for conversion).
    """
    # ── If it's a URL, try to download ─────────────────────────────────
    if update.message and update.message.text:
        url = update.message.text.strip()
        # Basic URL validation
        if not re.match(r"https?://\S+", url, re.I):
            await update.message.reply_text(
                "❌ That doesn't look like a valid link.\n\n"
                "Please send a link from a supported platform, or tap a button below.",
                reply_markup=main_menu_keyboard(),
            )
            return

        platform = detect_platform(url) or "unknown"
        status_msg = await update.message.reply_text(
            f"⏳ **Processing your link...**\n\n"
            f"📍 Platform: `{platform.capitalize()}`\n"
            f"📎 URL: `{url[:60]}{'…' if len(url) > 60 else ''}`\n\n"
            f"_Downloading & optimizing… please wait_ ⏱️",
            parse_mode="Markdown",
        )

        file_path, err = await download_media(url)

        if err:
            await status_msg.edit_text(
                f"{err}\n\nPlease check the link and try again, or pick a platform below:",
                reply_markup=main_menu_keyboard(),
            )
            return

        # Check file size
        size = await dl_size(file_path)
        if size > config.MAX_FILE_SIZE:
            await status_msg.edit_text(
                f"⚠️ File size (`{size / 1024 / 1024:.1f} MB`) exceeds Telegram's limit (45 MB).\n\n"
                f"Try using a conversion option to reduce size, or download from a different source.",
                reply_markup=main_menu_keyboard(),
            )
            dl_clean(file_path)
            return

        # Send the file
        await status_msg.edit_text("📤 **Uploading to Telegram…**", parse_mode="Markdown")

        try:
            with open(file_path, "rb") as f:
                await update.message.reply_document(
                    document=f,
                    caption=f"✅ **Download complete!**\n📌 Platform: `{platform.capitalize()}`\n🔗 [Source]({url})",
                    parse_mode="Markdown",
                )
            await status_msg.delete()
        except Exception as e:
            await status_msg.edit_text(f"❌ Upload failed: {str(e)}")
        finally:
            dl_clean(file_path)

    # ── If it's a media file (document/video) — store for conversion ──
    elif update.message and (update.message.document or update.message.video):
        file = update.message.document or update.message.video
        context.user_data["media_file_id"] = file.file_id
        context.user_data["media_file_name"] = getattr(file, "file_name", "media") or "media"

        await update.message.reply_text(
            "📎 **Media received!**\n\n"
            "Now choose a conversion option below:",
            reply_markup=conversion_only_keyboard(),
            parse_mode="Markdown",
        )

    else:
        await update.message.reply_text(
            "❓ Send me a **link** to download, or a **media file** to convert.\n\n"
            "Use the buttons below to get started:",
            reply_markup=main_menu_keyboard(),
        )


def conversion_only_keyboard() -> InlineKeyboardMarkup:
    """Keyboard with only conversion buttons."""
    kb = []
    convs = list(config.CONVERSIONS.items())
    for i in range(0, len(convs), 2):
        row = []
        for key, val in convs[i:i + 2]:
            row.append(InlineKeyboardButton(val["label"], callback_data=f"convert:{key}"))
        kb.append(row)
    kb.append([InlineKeyboardButton("🔙 Main Menu", callback_data="back_menu")])
    return InlineKeyboardMarkup(kb)


async def handle_media_for_conversion(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle media files sent for conversion (video/document)."""
    file = update.message.document or update.message.video
    if not file:
        return

    context.user_data["media_file_id"] = file.file_id
    context.user_data["media_file_name"] = getattr(file, "file_name", "media") or "media"

    await update.message.reply_text(
        "📎 **Media received!**\n\n"
        "Now choose a conversion option:",
        reply_markup=conversion_only_keyboard(),
        parse_mode="Markdown",
    )


# ════════════════════════════════════════════════════════════════════════
#  CALLBACK QUERY HANDLER
# ════════════════════════════════════════════════════════════════════════

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all inline button presses."""
    query = update.callback_query
    await query.answer()

    data = query.data

    # ── Navigation ──────────────────────────────────────────────────────
    if data == "help":
        await help_command(update, context)
        return

    if data == "about":
        await about(update, context)
        return

    if data == "back_menu":
        await query.edit_message_text(
            "🔙 **Main Menu** — Choose an option below:",
            reply_markup=main_menu_keyboard(),
            parse_mode="Markdown",
        )
        return

    if data == "send_link":
        await query.edit_message_text(
            "📤 **Send me a link!**\n\n"
            "Just paste any supported platform URL directly in the chat.\n\n"
            "Supported: Dailymotion, Vimeo, VK, TikTok, Reddit, Threads, Xiaohongshu & more!",
            reply_markup=main_menu_keyboard(),
            parse_mode="Markdown",
        )
        return

    # ── Platform Selection ──────────────────────────────────────────────
    if data.startswith("platform:"):
        platform_key = data.split(":", 1)[1]
        info = config.PLATFORMS.get(platform_key, {"label": platform_key.capitalize()})
        await query.edit_message_text(
            f"🌍 **{info['label']}**\n\n"
            f"📌 To download from **{info['label']}**, simply:\n"
            f"1️⃣ Copy a video/link from {info['label']}\n"
            f"2️⃣ Paste it here in the chat\n"
            f"3️⃣ I'll download and send it to you! 🚀\n\n"
            f"💡 *Tip: You can also paste any link directly without selecting a platform first.*",
            reply_markup=platform_keyboard(platform_key),
            parse_mode="Markdown",
        )
        return

    # ── Conversion Selection ────────────────────────────────────────────
    if data.startswith("convert:"):
        conv_key = data.split(":", 1)[1]
        conv_info = config.CONVERSIONS.get(conv_key)

        if not conv_info:
            await query.edit_message_text(
                "❌ Unknown conversion option.",
                reply_markup=main_menu_keyboard(),
            )
            return

        target = conv_info["to"]
        from_fmt = conv_info["from"]

        # Check if user has previously uploaded media
        media_file_id = context.user_data.get("media_file_id")
        media_file_name = context.user_data.get("media_file_name", "media")

        if from_fmt is not None:
            # Cross-format conversion requires a media file already sent
            if not media_file_id:
                await query.edit_message_text(
                    f"🔄 **{conv_info['label']}**\n\n"
                    f"Please **send me a `.{from_fmt}` file** first, then tap this button again.\n\n"
                    f"_I'll convert it to `.{target}` for you!_ 🎯",
                    reply_markup=main_menu_keyboard(),
                    parse_mode="Markdown",
                )
                return

            # Download the media file from Telegram
            file_obj = await context.bot.get_file(media_file_id)
            input_ext = Path(media_file_name).suffix or f".{from_fmt}"
            input_path = os.path.join(config.CONVERTED_DIR, f"input_{media_file_id}{input_ext}")
            await file_obj.download_to_drive(input_path)

            await query.edit_message_text(
                f"⏳ **Converting** `{media_file_name}` **→ `.{target}`**…\n\n"
                f"_This may take a moment_ ⏱️",
                parse_mode="Markdown",
            )

            output_path, err = await convert_media(input_path, target)
            conv_clean(input_path)  # remove input copy

            if err:
                await query.edit_message_text(
                    f"{err}\n\nPlease try again or choose another option.",
                    reply_markup=main_menu_keyboard(),
                )
                return

            # Check size
            size = await conv_size(output_path)
            if size > config.MAX_FILE_SIZE:
                await query.edit_message_text(
                    f"⚠️ Converted file (`{size / 1024 / 1024:.1f} MB`) exceeds Telegram's limit.\n"
                    f"Try a different format or lower quality.",
                    reply_markup=main_menu_keyboard(),
                )
                conv_clean(output_path)
                return

            # Send
            await query.edit_message_text("📤 **Uploading converted file…**", parse_mode="Markdown")
            try:
                with open(output_path, "rb") as f:
                    await query.message.reply_document(
                        document=f,
                        caption=f"✅ **Conversion complete!**\n"
                                f"🔄 `{media_file_name}` → `.{target}`\n"
                                f"📏 Size: `{size / 1024 / 1024:.1f} MB`",
                        parse_mode="Markdown",
                    )
                await query.edit_message_text(
                    "✅ **Done!** What would you like to do next?",
                    reply_markup=main_menu_keyboard(),
                )
            except Exception as e:
                await query.edit_message_text(f"❌ Upload failed: {str(e)}")
            finally:
                conv_clean(output_path)

        else:
            # Direct format conversion (no source check)
            if not media_file_id:
                await query.edit_message_text(
                    f"🎯 **{conv_info['label']}**\n\n"
                    f"Send me a **video or audio file** first, then tap this button.\n\n"
                    f"_I'll convert it to `.{target}` for you!_",
                    reply_markup=main_menu_keyboard(),
                    parse_mode="Markdown",
                )
                return

            # Same logic as above — download and convert
            file_obj = await context.bot.get_file(media_file_id)
            input_path = os.path.join(config.CONVERTED_DIR, f"input_{media_file_id}{Path(media_file_name).suffix or '.mp4'}")
            await file_obj.download_to_drive(input_path)

            await query.edit_message_text(
                f"⏳ **Converting to `.{target}`**…",
                parse_mode="Markdown",
            )

            output_path, err = await convert_media(input_path, target)
            conv_clean(input_path)

            if err:
                await query.edit_message_text(f"{err}", reply_markup=main_menu_keyboard())
                return

            size = await conv_size(output_path)
            if size > config.MAX_FILE_SIZE:
                await query.edit_message_text(
                    f"⚠️ File too large (`{size / 1024 / 1024:.1f} MB`).",
                    reply_markup=main_menu_keyboard(),
                )
                conv_clean(output_path)
                return

            await query.edit_message_text("📤 **Uploading…**", parse_mode="Markdown")
            try:
                with open(output_path, "rb") as f:
                    await query.message.reply_document(
                        document=f,
                        caption=f"✅ **Converted to `.{target}`**\n📏 Size: `{size / 1024 / 1024:.1f} MB`",
                        parse_mode="Markdown",
                    )
                await query.edit_message_text(
                    "✅ **Done!** Choose another option below:",
                    reply_markup=main_menu_keyboard(),
                )
            except Exception as e:
                await query.edit_message_text(f"❌ Upload failed: {str(e)}")
            finally:
                conv_clean(output_path)


# ════════════════════════════════════════════════════════════════════════
#  ERROR HANDLER
# ════════════════════════════════════════════════════════════════════════

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors and notify the user if possible."""
    print(f"❌ Error: {context.error}")
    if update and update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="⚠️ An unexpected error occurred. Please try again later.",
        )


# ════════════════════════════════════════════════════════════════════════
#  BUILD APPLICATION
# ════════════════════════════════════════════════════════════════════════

def build_application() -> Application:
    """Create and configure the Application instance."""
    app = (
        Application.builder()
        .token(config.BOT_TOKEN)
        .concurrent_updates(True)
        .build()
    )

    # ── Handlers ───────────────────────────────────────────────────────
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about))

    # Message handlers
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.ALL, handle_media_for_conversion))

    # Callback queries
    app.add_handler(CallbackQueryHandler(button_callback))

    # Errors
    app.add_error_handler(error_handler)

    return app
