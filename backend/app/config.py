from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://ledger:ledger@localhost:5432/ledger"
    sql_echo:     bool = False
    env:          str  = "development"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    @property
    def async_database_url(self) -> str:
        """
        Render (and most managed Postgres providers) give a URL starting with
        'postgresql://' or 'postgres://'.  asyncpg requires the
        'postgresql+asyncpg://' scheme.  This property normalises it so the
        app works in every environment without manual editing.
        """
        url = self.database_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()