"""History and favorites management for flightplans."""
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QSettings


@dataclass
class FlightplanEntry:
    """Entry for a flightplan in history or favorites."""
    file_path: str
    departure: str
    destination: str
    title: str
    last_opened: str  # ISO format datetime
    is_favorite: bool = False
    tags: list[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []

    @property
    def filename(self) -> str:
        """Returns just the filename."""
        return Path(self.file_path).name

    @property
    def route_display(self) -> str:
        """Returns route as DEP -> ARR."""
        return f"{self.departure} → {self.destination}"

    @property
    def last_opened_datetime(self) -> datetime:
        """Returns last_opened as datetime object."""
        return datetime.fromisoformat(self.last_opened)

    @property
    def last_opened_display(self) -> str:
        """Returns human-readable last opened time."""
        dt = self.last_opened_datetime
        now = datetime.now()
        delta = now - dt

        if delta.days == 0:
            if delta.seconds < 3600:
                minutes = delta.seconds // 60
                return f"{minutes}分前" if minutes > 0 else "たった今"
            else:
                hours = delta.seconds // 3600
                return f"{hours}時間前"
        elif delta.days == 1:
            return "昨日"
        elif delta.days < 7:
            return f"{delta.days}日前"
        else:
            return dt.strftime("%Y/%m/%d")


class HistoryManager:
    """Manages flightplan history and favorites."""

    MAX_HISTORY_ITEMS = 50

    def __init__(self, settings: QSettings | None = None):
        self.settings = settings or QSettings("MSFSFlightplanViewer", "FlightplanViewer")
        self._history: list[FlightplanEntry] = []
        self._favorites: list[FlightplanEntry] = []
        self._load()

    def _load(self):
        """Load history and favorites from settings."""
        # Load history
        history_data = self.settings.value("history", [])
        if history_data:
            self._history = [self._dict_to_entry(d) for d in history_data if d]

        # Load favorites
        favorites_data = self.settings.value("favorites", [])
        if favorites_data:
            self._favorites = [self._dict_to_entry(d) for d in favorites_data if d]

    def _save(self):
        """Save history and favorites to settings."""
        self.settings.setValue("history", [asdict(e) for e in self._history])
        self.settings.setValue("favorites", [asdict(e) for e in self._favorites])

    def _dict_to_entry(self, d: dict) -> FlightplanEntry:
        """Convert dictionary to FlightplanEntry."""
        return FlightplanEntry(
            file_path=d.get('file_path', ''),
            departure=d.get('departure', '----'),
            destination=d.get('destination', '----'),
            title=d.get('title', ''),
            last_opened=d.get('last_opened', datetime.now().isoformat()),
            is_favorite=d.get('is_favorite', False),
            tags=d.get('tags', [])
        )

    def add_to_history(
        self,
        file_path: str,
        departure: str,
        destination: str,
        title: str = ""
    ) -> FlightplanEntry:
        """
        Add a flightplan to history.

        Args:
            file_path: Path to the flightplan file
            departure: Departure airport ICAO
            destination: Destination airport ICAO
            title: Optional title

        Returns:
            The created or updated entry
        """
        # Check if already in history
        existing = self._find_in_history(file_path)
        if existing:
            # Update existing entry
            existing.last_opened = datetime.now().isoformat()
            existing.departure = departure
            existing.destination = destination
            if title:
                existing.title = title
            # Move to front
            self._history.remove(existing)
            self._history.insert(0, existing)
        else:
            # Create new entry
            entry = FlightplanEntry(
                file_path=file_path,
                departure=departure,
                destination=destination,
                title=title or Path(file_path).stem,
                last_opened=datetime.now().isoformat(),
                is_favorite=self._is_favorite(file_path)
            )
            self._history.insert(0, entry)
            existing = entry

        # Limit history size
        if len(self._history) > self.MAX_HISTORY_ITEMS:
            self._history = self._history[:self.MAX_HISTORY_ITEMS]

        self._save()
        return existing

    def _find_in_history(self, file_path: str) -> FlightplanEntry | None:
        """Find an entry in history by file path."""
        for entry in self._history:
            if entry.file_path == file_path:
                return entry
        return None

    def _is_favorite(self, file_path: str) -> bool:
        """Check if a file is in favorites."""
        return any(e.file_path == file_path for e in self._favorites)

    def get_history(self, limit: int | None = None) -> list[FlightplanEntry]:
        """
        Get history entries.

        Args:
            limit: Optional limit on number of entries

        Returns:
            List of history entries, most recent first
        """
        if limit:
            return self._history[:limit]
        return self._history.copy()

    def get_favorites(self) -> list[FlightplanEntry]:
        """Get all favorite entries."""
        return self._favorites.copy()

    def add_to_favorites(self, file_path: str) -> bool:
        """
        Add a flightplan to favorites.

        Args:
            file_path: Path to the flightplan file

        Returns:
            True if added, False if already in favorites
        """
        if self._is_favorite(file_path):
            return False

        # Find in history for details
        history_entry = self._find_in_history(file_path)
        if history_entry:
            entry = FlightplanEntry(
                file_path=history_entry.file_path,
                departure=history_entry.departure,
                destination=history_entry.destination,
                title=history_entry.title,
                last_opened=history_entry.last_opened,
                is_favorite=True,
                tags=history_entry.tags.copy()
            )
            history_entry.is_favorite = True
        else:
            # Create minimal entry
            entry = FlightplanEntry(
                file_path=file_path,
                departure="----",
                destination="----",
                title=Path(file_path).stem,
                last_opened=datetime.now().isoformat(),
                is_favorite=True
            )

        self._favorites.append(entry)
        self._save()
        return True

    def remove_from_favorites(self, file_path: str) -> bool:
        """
        Remove a flightplan from favorites.

        Args:
            file_path: Path to the flightplan file

        Returns:
            True if removed, False if not in favorites
        """
        for i, entry in enumerate(self._favorites):
            if entry.file_path == file_path:
                self._favorites.pop(i)
                # Update history entry
                history_entry = self._find_in_history(file_path)
                if history_entry:
                    history_entry.is_favorite = False
                self._save()
                return True
        return False

    def toggle_favorite(self, file_path: str) -> bool:
        """
        Toggle favorite status.

        Args:
            file_path: Path to the flightplan file

        Returns:
            True if now a favorite, False if no longer a favorite
        """
        if self._is_favorite(file_path):
            self.remove_from_favorites(file_path)
            return False
        else:
            self.add_to_favorites(file_path)
            return True

    def is_favorite(self, file_path: str) -> bool:
        """Check if a file is a favorite."""
        return self._is_favorite(file_path)

    def add_tag(self, file_path: str, tag: str):
        """Add a tag to a flightplan entry."""
        entry = self._find_in_history(file_path)
        if entry and tag not in entry.tags:
            entry.tags.append(tag)
            self._save()

        # Also update favorites if present
        for fav in self._favorites:
            if fav.file_path == file_path and tag not in fav.tags:
                fav.tags.append(tag)

    def remove_tag(self, file_path: str, tag: str):
        """Remove a tag from a flightplan entry."""
        entry = self._find_in_history(file_path)
        if entry and tag in entry.tags:
            entry.tags.remove(tag)
            self._save()

        for fav in self._favorites:
            if fav.file_path == file_path and tag in fav.tags:
                fav.tags.remove(tag)

    def clear_history(self):
        """Clear all history (but keep favorites)."""
        self._history = [e for e in self._history if e.is_favorite]
        self._save()

    def search_history(self, query: str) -> list[FlightplanEntry]:
        """
        Search history by query.

        Args:
            query: Search query (matches filename, route, title, tags)

        Returns:
            Matching entries
        """
        query = query.lower()
        results = []
        for entry in self._history:
            if (query in entry.filename.lower() or
                query in entry.departure.lower() or
                query in entry.destination.lower() or
                query in entry.title.lower() or
                any(query in tag.lower() for tag in entry.tags)):
                results.append(entry)
        return results
