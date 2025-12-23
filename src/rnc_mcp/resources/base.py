from abc import ABC, abstractmethod
from rnc_mcp.clients.base import CorpusClient


class CorpusResourceGenerator(ABC):
    """Abstract base class for resource generators."""

    def __init__(self, client: CorpusClient):
        """
        Initialize with any client implementing CorpusClient interface.
        """
        self.client = client

    @abstractmethod
    async def generate(self, corpus: str) -> str:
        """Generate a resource description string."""
        pass
