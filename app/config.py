from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # DDoS Protection Bot
    bot_token: str = ""
    admin_user_id: int = 0
    auto_block_threshold: int = 100

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
