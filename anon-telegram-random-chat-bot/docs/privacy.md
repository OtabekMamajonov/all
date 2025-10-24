# Privacy Policy

This project relays messages between anonymous chat partners. The bot never
discloses Telegram usernames, profile links, or numeric identifiers to the
opposite side. The system stores only the minimal metadata required to keep the
service running and deletes it automatically after the configured retention
period.

## Stored data

* Active session links: Telegram user identifiers mapped to a randomly
generated session identifier and the anonymous partner identifier.
* Block list: anonymous pairs that should never be matched again.
* Reports: masked identifiers and the anonymous session ID that triggered the
  report.

All values are stored inside a local SQLite database by default. Optional Redis
usage is limited to rate-limit counters with short TTLs.

## Retention

Ended session metadata is automatically removed after the configured
`SESSION_TTL_SEC`. When the value is set to `0`, the cleanup is disabled and
only explicit moderation actions remain.

## Logs

Application logs can be configured to mask Telegram user identifiers by setting
`MASK_USER_IDS=true`. Moderation exports must be handled manually and should be
wiped once review is complete.

## Third-party services

Video calls are implemented by generating a one-time Jitsi Meet room link.
Calls are hosted on the configured Jitsi deployment (default
`https://meet.jit.si`). Please review the upstream Jitsi privacy policy before
production use.
