from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Issue Tracking System"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DATABASE_URL: str 
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
