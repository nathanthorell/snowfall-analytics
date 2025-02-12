import json
from pathlib import Path

from .models import Config, StationConfig


def load_config(
    data_dir: Path | str = "data", config_path: Path | str | None = None
) -> Config:
    """
    Load configuration from files.

    Args:
        data_dir: Path to data directory
        config_path: Path to config.json file (defaults to package config)

    Returns:
        Loaded configuration
    """
    # Use default package config if no path provided
    if config_path is None:
        config_path = Path(__file__).parent / "config.json"

    # Load and parse station config
    with open(config_path) as f:
        raw_config = json.load(f)

    stations_config = StationConfig(**raw_config)

    return Config(data_dir=Path(data_dir), stations=stations_config)
