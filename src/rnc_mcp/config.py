import os
from typing import Optional, Dict
from dotenv import load_dotenv

from rnc_mcp.exceptions import RNCConfigError


# Load environment variables from .env file if it exists
load_dotenv()


class Config:
    RNC_BASE_URL: str = "https://ruscorpora.ru/api/v1"
    _RNC_TOKEN: Optional[str] = os.getenv("RNC_API_TOKEN")
    RNC_PAGE_DELAY: float = float(
        os.getenv("RNC_PAGE_DELAY", "0.5")
    )
    RNC_MAX_RETRIES: int = int(
        os.getenv("RNC_MAX_RETRIES", "3")
    )
    RNC_AUTH_CACHE_TTL: float = float(
        os.getenv("RNC_AUTH_CACHE_TTL", "300")
    )
    RNC_OAUTH_BASE_URL: str = os.getenv(
        "RNC_OAUTH_BASE_URL",
        "http://127.0.0.1:8000",
    )

    @classmethod
    def get_database_url(cls) -> str:
        """Resolve the OAuth database connection URL.

        Precedence: ``RNC_DATABASE_URL`` (any SQLAlchemy URL,
        e.g. ``postgresql://...``) → legacy
        ``RNC_OAUTH_DB_PATH`` (interpreted as a SQLite file)
        → SQLite at ``/tmp/oauth.db``.
        """
        url = os.getenv("RNC_DATABASE_URL")
        if url:
            return url
        legacy_path = os.getenv("RNC_OAUTH_DB_PATH")
        if legacy_path:
            return f"sqlite:///{legacy_path}"
        return "sqlite:////tmp/oauth.db"

    RNC_CORPORA: Dict[str, str] = {
        "MAIN": "Main",
        "PAPER": "Media (newspapers)",
        "POETIC": "Poetry",
        "SPOKEN": "Spoken",
        "DIALECT": "Dialect",
        "SCHOOL": "Educational",
        "SYNTAX": "SynTagRus",
        "MULTI": "Multimedia",
        "ACCENT": "Accentological",
        "MULTIPARC": "MultiPARC",
        "KIDS": "From 2 to 15",
        "CLASSICS": "Russian classics",
        "BLOGS": "Social networks",
        "PANCHRON": "Panchronic",
        "OLD_RUS": "Old East Slavic",
        "MID_RUS": "Middle Russian"
    }

    @classmethod
    def get_rnc_token(cls) -> str:
        if not cls._RNC_TOKEN:
            raise RNCConfigError(
                "RNC_API_TOKEN is not set. Please generate a token at "
                "https://ruscorpora.ru/accounts/profile/for-devs and set it "
                "in your environment variables."
            )
        return cls._RNC_TOKEN

    @staticmethod
    def rnc_headers(token: str) -> dict:
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
