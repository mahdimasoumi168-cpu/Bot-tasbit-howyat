from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str = Field(default="", validation_alias="BOT_TOKEN")
    database_url: str = Field(
        # Railway's persistent volume is mounted at /data. Keep the fallback DB there
        # so a missing DATABASE_URL does not silently put production data on ephemeral disk.
        default="sqlite+aiosqlite:////data/bot.db",
        validation_alias="DATABASE_URL",
    )
    admin_ids: str = Field(default="", validation_alias="ADMIN_IDS")
    support_telegram_id: int | None = Field(default=8937359321, validation_alias="SUPPORT_TELEGRAM_ID")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def admin_id_set(self) -> set[int]:
        result: set[int] = set()
        for raw in self.admin_ids.split(","):
            raw = raw.strip()
            if raw:
                try:
                    result.add(int(raw))
                except ValueError:
                    continue
        return result


@lru_cache
def get_settings() -> Settings:
    return Settings()
