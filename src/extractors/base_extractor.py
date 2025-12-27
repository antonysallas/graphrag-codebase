from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Generator, Optional


class BaseExtractor(ABC):
    """Abstract base class for code extractors."""

    schema_profile: str = "generic"  # Override in subclass

    @abstractmethod
    def extract(
        self, codebase_path: Path, repository_id: Optional[str] = None
    ) -> Generator[dict[str, Any], None, None]:
        """Extract entities from codebase.

        Yields:
            Dict with 'type' (node type) and 'properties' (node data)
        """
        pass

    @abstractmethod
    def extract_relationships(
        self, codebase_path: Path, repository_id: Optional[str] = None
    ) -> Generator[dict[str, Any], None, None]:
        """Extract relationships between entities.

        Yields:
            Dict with 'type', 'source', 'target', and optional 'properties'
        """
        pass

    def supported_extensions(self) -> list[str]:
        """File extensions this extractor handles."""
        return ["*"]
