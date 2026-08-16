import os
import yaml
from pydantic import BaseModel, ConfigDict
from typing import List

class SecurityConfig(BaseModel):
    jwt_secret_env_var: str = "BACKEND_JWT_SECRET"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    cors_origins: List[str] = ["*"]
    
class AppConfig(BaseModel):
    name: str = "FastAPI Backend"
    version: str = "1.0.0"
    port: int = 8000
    host: str = "0.0.0.0"
    database_url_env_var: str = "DATABASE_URL"

class BackendSettings(BaseModel):
    """Configuration loader for the FastAPI Layer (Part 11) using backend_config.yaml"""
    
    app: AppConfig = AppConfig()
    security: SecurityConfig = SecurityConfig()
    
    model_config = ConfigDict(extra="ignore")
    
    @classmethod
    def load(cls, config_path: str = "backend/backend_config.yaml") -> "BackendSettings":
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                data = yaml.safe_load(f)
                if data:
                    return cls(**data)
        return cls()
        
    @property
    def jwt_secret(self) -> str:
        """Fetches the real JWT secret from the environment overriding configs securely."""
        return os.getenv(self.security.jwt_secret_env_var, "unsafe-default-dev-secret-replace-me")

    @property
    def database_url(self) -> str:
        """Fetches the database connection string from the environment."""
        # SQLite used as default fallback during Stage 7 per user approval
        return os.getenv(self.app.database_url_env_var, "sqlite:///./phase2_app.db")
