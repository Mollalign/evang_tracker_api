from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    SMTP_EMAIL: str
    SMTP_PASSWORD: str
    SMTP_SERVER: str
    SMTP_PORT: str


    class Config:
        env_file = ".env"

settings = Settings()