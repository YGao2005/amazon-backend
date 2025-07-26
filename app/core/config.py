import os
import json
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    APP_NAME: str = os.getenv("APP_NAME", "SmartRecipeApp")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    API_PREFIX: str = os.getenv("API_PREFIX", "/api/v1")
    
    # Firebase Configuration
    FIREBASE_PROJECT_ID: str = os.getenv("FIREBASE_PROJECT_ID", "")
    FIREBASE_CREDENTIALS_PATH: str = os.getenv("FIREBASE_CREDENTIALS_PATH", "./firebase-credentials.json")
    
    # AI Service API Keys
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    @property
    def firebase_credentials(self) -> Dict[str, Any]:
        """
        Load Firebase credentials from JSON file.
        """
        try:
            with open(self.FIREBASE_CREDENTIALS_PATH, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: Firebase credentials file not found at {self.FIREBASE_CREDENTIALS_PATH}")
            # Return dummy credentials for testing
            return {
                "type": "service_account",
                "project_id": self.FIREBASE_PROJECT_ID,
                "private_key_id": "dummy",
                "private_key": "dummy",
                "client_email": "dummy@dummy.com",
                "client_id": "dummy",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": "dummy"
            }
        except json.JSONDecodeError as e:
            print(f"Warning: Invalid JSON in Firebase credentials file: {e}")
            return {
                "type": "service_account",
                "project_id": self.FIREBASE_PROJECT_ID,
                "private_key_id": "dummy",
                "private_key": "dummy",
                "client_email": "dummy@dummy.com",
                "client_id": "dummy",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": "dummy"
            }

# Create settings instance
settings = Settings()