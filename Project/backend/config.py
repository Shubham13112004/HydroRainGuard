from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    database_url: str = (
        "sqlite+aiosqlite:///./hydro_rain_guard.db"
    )

    openweather_api_key: str = "demo"

    frontend_url: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
