from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openweather_api_key: str = 'demo'
    database_url: str = 'sqlite+aiosqlite:///./hydro_rain_guard.db'
    frontend_url: str = 'http://localhost:3000'
    
    class Config:
        env_file = '.env'

settings = Settings()
