import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # PostgreSQL configuration
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "dev")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "devpass")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "devdb")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    
    # Database URL construction
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )


settings = Settings()
