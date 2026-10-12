from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    EMAIL_HOST: str
    EMAIL_PORT: int
    EMAIL_USERNAME: str
    EMAIL_PASSWORD: SecretStr
    FRONTEND_URL: str

    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int

    RABBIT_HOST: str
    RABBIT_USER: str
    RABBIT_PASS: SecretStr
    RABBIT_PORT: int

    SECRET_KEY: str
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str

    ACCESS_MAX_AGE: int
    REFRESH_MAX_AGE: int

    HMAC_KEY: str

    @property
    def db_url(self):
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def db_url_sync(self):
        return f"postgresql://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def redis_url(self):
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def rabbit_url(self):
        return f"amqp://{self.RABBIT_USER}:{self.RABBIT_PASS.get_secret_value()}@{self.RABBIT_HOST}:{self.RABBIT_PORT}/"


settings = Settings()
