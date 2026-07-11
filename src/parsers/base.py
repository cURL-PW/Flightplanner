"""Base class for flightplan parsers."""
from abc import ABC, abstractmethod
from pathlib import Path

from ..models import Flightplan


class FlightplanParser(ABC):
    """Abstract base class for flightplan parsers."""

    @property
    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """Returns list of supported file extensions."""
        pass

    @abstractmethod
    def parse(self, file_path: Path) -> Flightplan | None:
        """Parse a flightplan file and return a Flightplan object."""
        pass

    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file."""
        return file_path.suffix.lower() in self.supported_extensions
