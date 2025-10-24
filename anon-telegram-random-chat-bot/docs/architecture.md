# Architecture Overview

The anonymous chat bot is composed of three main layers.

1. **Transport** – The aiogram 3 dispatcher handles Telegram updates and routes
   them to command- and relay-specific handlers. Each handler uses dependency
   injection to access shared services.
2. **Domain services** – The `MatchingService` manages the waiting queue and the
   lifecycle of anonymous sessions. The `RateLimiter` abstracts over Redis or an
   in-memory fallback to protect the bot from spam.
3. **Persistence** – SQLite stores active sessions, ended session metadata,
   blocklists, and moderation reports. Optional Redis is used only for
   rate-limit counters.

## Data flow

* `/find` pushes a user into the matching queue. When the queue already contains
  a compatible partner, both users are paired, a random `session_id` is created,
  and the dispatcher notifies both parties.
* Messages exchanged during an active session are relayed with fresh send_* API
  calls. The bot never forwards messages directly, preventing accidental
  leakage of metadata.
* `/end`, `/block`, and `/next` terminate the session. `/block` also adds a
  permanent entry to the block list so the same pair is not matched again.
* `/video` produces a one-time Jitsi Meet URL bound to the current session ID.
* `/report` stores a masked report entry for later moderation.

## Background cleanup

The storage layer provides a periodic cleanup task that removes ended session
metadata older than the configured `SESSION_TTL_SEC`. The task is scheduled from
`app.main` using `asyncio.create_task` and gracefully cancelled during shutdown.

## Error handling

Handlers include defensive checks to keep the bot idempotent. All operational
errors are logged via the shared logging configuration. Telegram API calls are
wrapped with retry helpers to gracefully handle transient failures.
