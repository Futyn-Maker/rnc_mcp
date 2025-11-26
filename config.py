import os
from typing import Optional


class Config:
    BASE_URL: str = "https://ruscorpora.ru/api/v1"
    _RNC_TOKEN: Optional[str] = os.getenv("RNC_API_TOKEN")

    @classmethod
    def get_token(cls) -> str:
        if not cls._RNC_TOKEN:
            raise ValueError(
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
