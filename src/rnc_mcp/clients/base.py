from abc import ABC, abstractmethod
from typing import Dict, Any


class CorpusClient(ABC):
    """Abstract base class for corpus API clients."""

    @abstractmethod
    async def execute_concordance(
            self, payload: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Execute a search query against the corpus."""
        pass

    @abstractmethod
    async def get_corpus_config(self, corpus_type: str) -> Dict[str, Any]:
        """Fetch configuration for a specific corpus."""
        pass

    @abstractmethod
    async def get_attributes(self, corpus_type: str,
                             attr_type: str) -> Dict[str, Any]:
        """Fetch grammatical or semantic attributes."""
        pass
