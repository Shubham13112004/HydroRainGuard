from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    database_url: str = (
        "sqlite+aiosqlite:///./hydro_rain_guard.db"
    )

    openweather_api_key: str = "demo"

    frontend_url: str = "http://localhost:3000"

    # Comma separated list of allowed browser origins.
    # Example:
    # CORS_ORIGINS=https://hydro-rain-guard.vercel.app,http://localhost:3000
    cors_origins: str = (
        "http://localhost:3000,"
        "https://hydro-rain-guard.vercel.app,"
        "https://hydro-rain-guard-mhus.vercel.app"
    )

    # Optional shared secret for the maintenance endpoints
    # (POST /api/init-db and GET /api/assessments).
    # When left empty, /api/init-db is disabled in production
    # and /api/assessments returns redacted records.
    admin_token: str = ""

    # "development" enables the unauthenticated maintenance
    # helpers so `uvicorn main:app --reload` just works locally.
    environment: str = "development"

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            o.strip()
            for o in self.cors_origins.split(",")
            if o.strip()
        ]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in (
            "production",
            "prod",
        )


settings = Settings()
