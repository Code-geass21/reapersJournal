from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str

    # FIX FOR BUG 65: No default string here makes this strictly required by Pydantic.
    # If it's missing from the environment, the app will refuse to start.
    jwt_secret: str

    tz: str = "Asia/Kolkata"
    price_refresh_secs: int = 300
    twelvedata_api_key: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
