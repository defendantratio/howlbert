# Deploying Howlbert (24/7 VPS)

Minimal ops guide for running the bot on a small Linux VPS with auto-restart.

## Requirements

- Python 3.11+ (3.13 works)
- A Discord bot token in `.env`
- Optional: `BOT_DISPLAY_NAME=Howlbert`, `STATUS_CHANNEL_ID` for a `#bot-status` channel

## First deploy

```bash
git clone <your-repo-url> fable
cd fable
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env; DISCORD_TOKEN, BOT_DISPLAY_NAME, TEST_GUILD_ID (remove for production), STATUS_CHANNEL_ID
python main.py   # smoke test, then Ctrl+C
```

## systemd service (auto-restart)

Create `/etc/systemd/system/howlbert.service`:

```ini
[Unit]
Description=Howlbert Discord bot
After=network.target

[Service]
Type=simple
User=howlbert
WorkingDirectory=/home/howlbert/fable
Environment=PATH=/home/howlbert/fable/.venv/bin
ExecStart=/home/howlbert/fable/.venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable howlbert
sudo systemctl start howlbert
sudo systemctl status howlbert
```

Logs: `journalctl -u howlbert -f`

## Bot-status channel

1. Create `#bot-status` (staff-only read is fine).
2. Copy the channel ID into `.env` as `STATUS_CHANNEL_ID=...`.
3. On each startup Howlbert posts **Howlbert Online** with guild sync mode.
4. On shutdown (Ctrl+C or process stop) it posts **Howlbert Offline** to the same channel.

Players still need channel mentions for consent buttons; DMs are best-effort if the user allows them.

## Production slash commands

Remove `TEST_GUILD_ID` from `.env` when you want global commands. Global sync can take up to ~1 hour on first deploy.

## Database backup

SQLite file: `fable/fable.db`. Copy it nightly:

```bash
cp fable.db "fable-$(date +%F).db"
```

## Ko-fi webhook (optional)

If you run the shop webhook, open port `KOFI_WEBHOOK_PORT` (default 8080) and point Ko-fi at your VPS URL. See `docs/KOFI_SHOP.md`.
