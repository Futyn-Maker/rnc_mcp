import os
from typing import Optional, Dict
from dotenv import load_dotenv

from rnc_mcp.exceptions import RNCConfigError


# Load environment variables from .env file if it exists
load_dotenv()


class Config:
    BASE_URL: str = "https://ruscorpora.ru/api/v1"
    _RNC_TOKEN: Optional[str] = os.getenv("RNC_API_TOKEN")

    CORPORA: Dict[str, str] = {
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
        "BLOGS": "Social networks"
    }

    @classmethod
    def get_token(cls) -> str:
        if not cls._RNC_TOKEN:
            raise RNCConfigError(
                "RNC_API_TOKEN is not set. Please generate a token at "
                "https://ruscorpora.ru/accounts/profile/for-devs and set it "
                "in your environment variables."
            )
        return cls._RNC_TOKEN

    @classmethod
    def headers(cls) -> dict:
        return {
            "Authorization": f"Bearer {cls.get_token()}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
