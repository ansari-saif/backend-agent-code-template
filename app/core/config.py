import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Prefer explicit DATABASE_URL; fall back to local SQLite for dev
    DATABASE_URL: str = os.getenv("DATABASE_URL") or "sqlite:///./diary.db"


settings = Settings()