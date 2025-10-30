"""Application configuration module."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database Configuration
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "gemini_cache"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    
    # Database Pool Configuration
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600
    DB_POOL_PRE_PING: bool = True
    
    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # Gemini API Configuration
    GEMINI_API_KEY: str = ""
    
    # Application Configuration
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    
    # CORS Configuration
    CORS_ENABLED: bool = True
    CORS_ORIGINS: str = "*"
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: str = "*"
    CORS_HEADERS: str = "*"
    
    @property
    def cors_origins_list(self) -> list:
        """Parse CORS origins from comma-separated string."""
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    @property
    def cors_methods_list(self) -> list:
        """Parse CORS methods from comma-separated string."""
        if self.CORS_METHODS == "*":
            return ["*"]
        return [method.strip() for method in self.CORS_METHODS.split(",")]
    
    @property
    def cors_headers_list(self) -> list:
        """Parse CORS headers from comma-separated string."""
        if self.CORS_HEADERS == "*":
            return ["*"]
        return [header.strip() for header in self.CORS_HEADERS.split(",")]
    
    @property
    def database_url(self) -> str:
        """Construct PostgreSQL connection URL."""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
