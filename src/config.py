"""Loads environment variables. Fails fast with a clear message if a required
var is missing.
"""
import os
from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    val = os.getenv(name)
    if not val:
        raise RuntimeError(
            f"Required environment variable {name!r} is missing. "
            "Set it in .env (local) or as a GitHub Actions secret."
        )
    return val


def _optional(name: str, default: str = "") -> str:
    return os.getenv(name, default) or default


ANTHROPIC_API_KEY: str = _require("ANTHROPIC_API_KEY")
CLAUDE_MODEL: str = _optional("CLAUDE_MODEL", "claude-sonnet-4-6")
NEWSAPI_KEY: str = _optional("NEWSAPI_KEY", "")
TELEGRAM_BOT_TOKEN: str = _optional("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID: str = _optional("TELEGRAM_CHAT_ID", "")
