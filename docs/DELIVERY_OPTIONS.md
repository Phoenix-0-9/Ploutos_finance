# Delivery Options

Pick one (or more) before building `src/storage/notify.py`. Ask the user
which they want — don't assume.

## Option A — Just commit to the repo (simplest, no extra setup)

GitHub Actions writes `output/latest_forecast.md` and commits it back to
the repo daily. You read it by opening the repo / file on your phone via
GitHub's app or browser. Zero extra services, but not a "push"
notification.

## Option B — Telegram bot push (recommended for a daily ping)

1. Create a bot via `@BotFinder`/`@BotFather` on Telegram, get a bot
   token.
2. Message the bot once, get your `chat_id` (via
   `https://api.telegram.org/bot<TOKEN>/getUpdates`).
3. `notify.py` posts to:
   `https://api.telegram.org/bot<TOKEN>/sendMessage` with
   `chat_id` + `text` = rendered markdown summary.
4. Store `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` as GitHub Actions
   secrets.

This is free, fast to set up (~5 min), and gives you an actual phone
notification daily.

## Option C — Email

Use a transactional email service (e.g. Resend, SendGrid free tier, or
just SMTP via Gmail app password) to email
`output/latest_forecast.md` (rendered as HTML) to yourself daily.
Slightly more setup than Telegram, but lands in an inbox you already
check.

## Option D — Google Sheet

`notify.py` appends a row (date, spot rate, base/bull/bear midpoints) to
a Google Sheet via the Sheets API + a service account. Good if you want
to chart the forecast history over time. More setup overhead (service
account JSON, sharing the sheet) — combine with Option A or B for actual
notifications, since a sheet update won't ping you.

## Recommendation

Start with **Option A + Option B** (Telegram): commit the file for
history/auditability, and get a Telegram push for the daily nudge. Add
Option D later if you want charts.
