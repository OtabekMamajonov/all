from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

try:  # pragma: no cover - prefer pydantic when available
    from pydantic import Field
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ModuleNotFoundError:  # pragma: no cover - lightweight fallback
    class BaseSettings:  # type: ignore[override]
        def __init__(self, **data: object) -> None:
            for key, value in data.items():
                setattr(self, key, value)

    class Field:  # type: ignore[override]
        def __init__(self, default: object, alias: Optional[str] = None) -> None:
            self.default = default
            self.alias = alias

    class SettingsConfigDict(dict):  # type: ignore[override]
        pass

    def _env(key: str, default: str | None = None) -> str | None:
        return os.getenv(key, default)

    class Settings(BaseSettings):
        def __init__(self) -> None:
            self.bot_token = _env("BOT_TOKEN", "")
            self.redis_url = _env("REDIS_URL")
            self.database_path = _env("DATABASE_PATH", "./data/anon.sqlite3")
            self.jitsi_host = _env("JITSI_HOST", "https://meet.jit.si")
            self.rate_limit_msg_per_sec = float(_env("RATE_LIMIT_MSG_PER_SEC", "1") or 1)
            self.find_debounce_sec = int(_env("FIND_DEBOUNCE_SEC", "8") or 8)
            self.session_ttl_sec = int(_env("SESSION_TTL_SEC", "0") or 0)
            self.log_level = _env("LOG_LEVEL", "INFO")
            self.mask_user_ids = (_env("MASK_USER_IDS", "true") or "true").lower() == "true"
            self.mask_salt = _env("MASK_SALT")
            self.cleanup_interval_sec = int(_env("CLEANUP_INTERVAL_SEC", "600") or 600)

    def get_settings() -> Settings:
        return Settings()

else:

    class Settings(BaseSettings):
        bot_token: str = Field(..., alias="BOT_TOKEN")
        redis_url: Optional[str] = Field(None, alias="REDIS_URL")
        database_path: str = Field("./data/anon.sqlite3", alias="DATABASE_PATH")
        jitsi_host: str = Field("https://meet.jit.si", alias="JITSI_HOST")
        rate_limit_msg_per_sec: float = Field(1.0, alias="RATE_LIMIT_MSG_PER_SEC")
        find_debounce_sec: int = Field(8, alias="FIND_DEBOUNCE_SEC")
        session_ttl_sec: int = Field(0, alias="SESSION_TTL_SEC")
        log_level: str = Field("INFO", alias="LOG_LEVEL")
        mask_user_ids: bool = Field(True, alias="MASK_USER_IDS")
        mask_salt: Optional[str] = Field(None, alias="MASK_SALT")
        cleanup_interval_sec: int = Field(600, alias="CLEANUP_INTERVAL_SEC")

        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            case_sensitive=False,
            extra="ignore",
        )


    @lru_cache()
    def get_settings() -> Settings:
        return Settings()  # type: ignore[call-arg]


__all__ = ["Settings", "get_settings"]
