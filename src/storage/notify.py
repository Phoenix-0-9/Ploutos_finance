"""Sends the latest forecast to a Telegram bot.
Setup: create a bot via @BotFather, get the token, message the bot once,
then visit https://api.telegram.org/bot<TOKEN>/getUpdates to get your chat_id.
Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env.
"""
import logging
from pathlib import Path

import httpx

from src import config

logger = logging.getLogger(__name__)

LATEST_MD = Path(__file__).parent.parent.parent / "output" / "latest_forecast.md"
_TELEGRAM_URL = "https://api.telegram.org/bot{token}/sendMessage"
_CHUNK_SIZE = 4096  # Telegram hard limit per message


def _split_chunks(text: str) -> list[str]:
    """Split text into chunks <= _CHUNK_SIZE, breaking at paragraph boundaries."""
    chunks = []
    current = ""
    for paragraph in text.split("\n\n"):
        block = paragraph + "\n\n"
        if len(current) + len(block) <= _CHUNK_SIZE:
            current += block
        else:
            if current:
                chunks.append(current.rstrip())
            # If a single paragraph exceeds the limit, hard-split it
            while len(block) > _CHUNK_SIZE:
                chunks.append(block[:_CHUNK_SIZE])
                block = block[_CHUNK_SIZE:]
            current = block
    if current.strip():
        chunks.append(current.rstrip())
    return chunks


def notify(markdown_path: str = str(LATEST_MD)) -> None:
    token = config.TELEGRAM_BOT_TOKEN
    chat_id = config.TELEGRAM_CHAT_ID

    if not token or not chat_id:
        logger.info("TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID not set — skipping Telegram.")
        return

    text = Path(markdown_path).read_text(encoding="utf-8")
    chunks = _split_chunks(text)

    try:
        for i, chunk in enumerate(chunks, 1):
            r = httpx.post(
                _TELEGRAM_URL.format(token=token),
                json={"chat_id": chat_id, "text": chunk, "parse_mode": "Markdown"},
                timeout=20,
            )
            r.raise_for_status()
        logger.info("Telegram notification sent (%d message(s))", len(chunks))
    except Exception as e:
        logger.warning("Telegram notification failed: %s (non-fatal)", e)
