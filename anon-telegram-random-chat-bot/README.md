# Anonymous Telegram Random Chat Bot

> Anonymous matchmaking, safe message relay, and moderation tooling in one
> aiogram 3 project.

## TL;DR

* `/find` pairs users randomly without revealing Telegram identities.
* Messages are re-sent by the bot (no forwards) and rate-limited to reduce spam.
* `/end`, `/next`, `/block`, `/report`, and `/video` manage the session lifecycle.
* SQLite stores only minimal metadata. Optional Redis strengthens rate limiting.
* Docker and systemd unit files are provided for painless deployment.

## Features

* **Anonymous matching** – Users never see each other's user ID, username, or profile links.
* **Content relay** – Text, photos, voice, video, documents, and stickers are re-sent with fresh API calls.
* **Session control** – `/end` and `/next` gracefully stop chats; `/block` prevents future matches between the same pair.
* **Moderation** – `/report` logs a masked entry for follow-up. See [docs/privacy.md](docs/privacy.md).
* **Video rooms** – `/video` generates one-time Jitsi Meet links per active session.
* **Anti-spam** – Configurable rate limits for messages and matchmaking. Works with Redis or an in-memory fallback.
* **Data retention** – Optional TTL cleanup for ended session metadata.
* **Observability** – Structured logging with optional user-id masking.
* **Quality gates** – pytest suite, black, and ruff enforced via pre-commit hooks.

## Project layout

```
app/               # Bot code (config, storage, handlers, relay, utils)
docs/              # Architecture and privacy documentation
deploy/            # Docker and systemd deployment templates
tests/             # pytest-based unit tests
```

## Requirements

* Python 3.11+
* Telegram bot token (`BOT_TOKEN`)
* Optional: Redis instance for distributed rate limiting

Install dependencies into a virtual environment:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

1. Copy `.env.example` to `.env` and fill in at least `BOT_TOKEN`.
2. Optional settings:
   * `REDIS_URL` – e.g. `redis://localhost:6379/0`
   * `DATABASE_PATH` – SQLite file (default `./data/anon.sqlite3`)
   * `SESSION_TTL_SEC` – Retention time for ended session metadata (`0` disables cleanup)
   * `MASK_USER_IDS` / `MASK_SALT` – Control how report logs are anonymised
   * `RATE_LIMIT_MSG_PER_SEC` and `FIND_DEBOUNCE_SEC` – Tune anti-spam behaviour

## Running locally

```bash
python -m app.main
```

The bot will start polling. Hit `/start` in Telegram to see the menu.

Run the test suite:

```bash
pytest -q
```

## Deployment options

### Systemd

1. Sync the repository to `/opt/anon-telegram-random-chat-bot` (or similar).
2. Create a Python virtualenv in that directory and install requirements.
3. Copy `.env` with production secrets and adjust file permissions.
4. Install `deploy/systemd.service` to `/etc/systemd/system/anon-chat.service` and
   update paths if necessary.
5. Reload daemons and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now anon-chat.service
```

Logs appear in `journalctl -u anon-chat.service`. Consider adding a logrotate rule
if redirecting logs to files.

### Docker

Build and run with the provided compose file (includes optional Redis):

```bash
docker compose up -d --build
```

Mount a volume for the `data/` folder to persist SQLite data and edit `.env` to
match your environment. Remove the `redis` service if you prefer the in-memory
fallback.

## Moderation workflow

* `/report` stores a masked entry containing reporter, reported partner, session
  ID, and timestamp.
* Moderators can inspect the SQLite database (`reports` table) or export via a
  simple query.
* Set `MASK_USER_IDS=false` temporarily if you must reveal identities (not
  recommended for production).

## Privacy & safety

* Forwarding is disabled – all payloads are re-sent by the bot.
* Session IDs are random and not guessable.
* Optional cleanup removes historical session metadata after the configured TTL.
* See [docs/privacy.md](docs/privacy.md) for the detailed policy.
* Video calls are delegated to Jitsi; the bot only distributes a link.

## Troubleshooting

* Ensure the bot token is valid and `BOT_TOKEN` is set.
* If Redis is configured, check connectivity and credentials.
* For flood waits or `Too Many Requests`, lower `RATE_LIMIT_MSG_PER_SEC`.
* Run `pytest` to confirm the codebase is healthy after changes.

## License

Released under the [MIT License](LICENSE).
