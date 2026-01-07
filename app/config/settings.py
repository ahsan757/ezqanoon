try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:
    from pydantic import BaseSettings
    SettingsConfigDict = None


class Settings(BaseSettings):
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4.1-mini"

    # PostgreSQL connection URL, e.g.
    # postgresql://user:password@localhost:5432/ezqanoon
    DATABASE_URL: str

    SINDH_VECTOR_STORE_ID: str
    PUNJAB_VECTOR_STORE_ID: str
    KPK_VECTOR_STORE_ID: str
    BALOCHISTAN_VECTOR_STORE_ID: str
    KASHMIR_VECTOR_STORE_ID: str
    GBA_VECTOR_STORE_ID: str
    NATIONAL_VECTOR_STORE_ID: str
    FEDERAL_VECTOR_STORE_ID:str
    
    # API URL for frontend
    API_URL: str

    if SettingsConfigDict:
        # Pydantic v2 syntax
        model_config = SettingsConfigDict(
            env_file=".env",
            extra="ignore"  # Ignore extra fields from environment
        )
    else:
        # Pydantic v1 syntax
        class Config:
            env_file = ".env"
            extra = "ignore"  # Ignore extra fields from environment


settings = Settings()

