from abc import ABC, abstractmethod


class TokenValidator(ABC):
    """Abstract base class for token validators."""

    @abstractmethod
    async def validate(self, token: str) -> bool:
        """Validate a token. Returns True if valid, False otherwise."""
        pass
