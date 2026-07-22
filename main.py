#!/usr/bin/env python3
"""
All Link Download Bot — Entry Point

Deployment modes:
  • polling  – for Render Background Worker (free tier friendly)
  • webhook  – for Render Web Service (requires RENDER_EXTERNAL_URL)
"""

import os
import sys

from config import config
from bot import build_application


def main():
    app = build_application()

    if config.MODE == "webhook":
        # ── Webhook mode (Render Web Service) ──────────────────────────
        webhook_url = config.WEBHOOK_URL or config.RENDER_EXTERNAL_URL
        if not webhook_url:
            print("❌ WEBHOOK_URL or RENDER_EXTERNAL_URL must be set in webhook mode.")
            sys.exit(1)

        if not webhook_url.startswith("https://"):
            print("❌ Webhook URL must use HTTPS.")
            sys.exit(1)

        port = config.PORT
        print(f"🌐 Starting webhook on port {port}")
        print(f"🔗 Webhook URL: {webhook_url}")

        app.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=config.BOT_TOKEN,
            webhook_url=f"{webhook_url}/{config.BOT_TOKEN}",
        )
    else:
        # ── Polling mode (Render Background Worker) ────────────────────
        print("🚀 All Link Download Bot — Starting (polling mode)")
        print(f"👑 Owner: @{config.OWNER_USERNAME}")
        print("⏳ Waiting for messages...")
        app.run_polling(allowed_updates=None)


if __name__ == "__main__":
    main()
