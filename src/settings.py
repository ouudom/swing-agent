"""Central config for swing-agent services. Not yet wired into callers — see
docs/framework-migration-plan.md Phase 0. New code should import `settings` from here
instead of reading `os.environ` directly.
"""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Postgres
    database_url: str | None = None
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "swing_agent"
    postgres_user: str = "swing_agent"
    postgres_password: str = "swing_agent_dev_password"

    # Redis (Phase 1)
    redis_url: str = "redis://localhost:6379/0"

    # External data providers
    twelve_data_key: str | None = None
    fred_key: str | None = None

    # MCP
    mcp_host: str = "0.0.0.0"
    mcp_native_port: int = 8766
    mcp_auth_token: str = "dev-token"

    # Dashboard
    dashboard_host: str = "0.0.0.0"
    dashboard_port: int = 8888

    # Pipeline
    swing_agent_repo_root: str | None = None
    swing_db_backend: str = "postgres"
    pipeline_run_log: str | None = None

    def pg_dsn(self) -> str:
        # +psycopg forces the psycopg v3 driver (what this project installs via
        # `psycopg[binary]`) — a bare "postgresql://" DSN makes SQLAlchemy default to
        # psycopg2, which isn't installed anywhere in this stack.
        if self.database_url:
            url = self.database_url
            if url.startswith("postgresql://"):
                url = "postgresql+psycopg://" + url[len("postgresql://") :]
            return url
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
