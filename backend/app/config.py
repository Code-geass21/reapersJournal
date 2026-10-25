from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    jwt_secret: str
    tz: str = "Asia/Kolkata"
    price_refresh_secs: int = 30

    class Config:
        env_file = ".env"

settings = Settings()
