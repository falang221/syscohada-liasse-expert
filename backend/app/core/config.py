from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "SYSCOHADA Liasse-Expert"
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/syscohada_db"

    class Config:
        case_sensitive = True

settings = Settings()
