from pydantic import BaseSettings, Field, SecretStr


class Settings(BaseSettings):
    database_host: str = Field(..., env="DATABASE_HOST")
    database_port: int = Field(..., env="DATABASE_PORT")
    database_name: str = Field(..., env="DATABASE_NAME")
    database_user: str = Field(..., env="DATABASE_USER")
    database_password: str = Field(..., env="DATABASE_PASSWORD")
    telegram_token: SecretStr = Field(..., env="TELEGRAM_TOKEN")
    chat_id: int = Field(..., env="CHAT_ID")

    @property
    def database_url(self):
        return f"postgresql://{self.database_user}:{self.database_password}@{self.database_host}:{self.database_port}/{self.database_name}"

    @property
    def async_database_url(self):
        return f"postgresql+asyncpg://{self.database_user}:{self.database_password}@{self.database_host}:{self.database_port}/{self.database_name}"

    class Config:
        env_file = ".env"


settings = Settings()
