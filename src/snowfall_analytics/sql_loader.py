from pathlib import Path
from typing import Dict


class SQLLoader:
    """Manages SQL file loading"""

    def __init__(self, sql_dir: Path):
        """
        Initialize SQL loader

        Args:
            sql_dir: Path to directory containing SQL files
        """
        self.sql_dir = sql_dir
        self._cache: Dict[str, str] = {}

    def get_query(self, name: str) -> str:
        """
        Get SQL query by name

        Args:
            name: Name of SQL file (without .sql)

        Returns:
            SQL query string
        """
        if name not in self._cache:
            file_path = self.sql_dir / f"{name}.sql"
            if not file_path.exists():
                raise FileNotFoundError(f"SQL file not found: {file_path}")
            self._cache[name] = file_path.read_text()
        return self._cache[name]
