from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    jwt_secret: str
    tz: str = "Asia/Kolkata"
    price_refresh_secs: int = 300  # Default to 5 mins
    twelvedata_api_key: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
