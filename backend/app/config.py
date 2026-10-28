from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    jwt_secret: str
    tz: str = "Asia/Kolkata"
    price_refresh_secs: int = 3600  # Default to 1 hour
    alpha_vantage_api_key: str = "" # <-- Add this line

    class Config:
        env_file = ".env"

settings = Settings()
