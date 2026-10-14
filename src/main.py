"""Orchestrator entry point.
Run with: python -m src.main

Pipeline: build_snapshot -> run_forecast -> store -> notify
Exits non-zero only if the forecaster step itself fails.
"""
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
logger = logging.getLogger(__name__)


def main() -> None:
    # Import config early to fail fast if ANTHROPIC_API_KEY is missing.
    from src import config  # noqa: F401

    from src.compiler.build_snapshot import build_snapshot
    from src.forecaster.run_forecast import run_forecast
    from src.storage.history_store import store
    from src.storage.notify import notify

    logger.info("=== GBP/INR Forecast Pipeline starting ===")

    logger.info("Step 1: Building snapshot from collectors...")
    snapshot = build_snapshot()
    logger.info("Snapshot built for %s", snapshot["date"])

    logger.info("Step 2: Running forecast via Claude API (%s)...", config.CLAUDE_MODEL)
    forecast = run_forecast(snapshot)
    logger.info("Forecast complete.")

    logger.info("Step 3: Storing results...")
    store(snapshot, forecast)

    logger.info("Step 4: Sending Telegram notification...")
    notify()

    logger.info("=== Pipeline complete ===")


if __name__ == "__main__":
    main()
