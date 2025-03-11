import json
from pathlib import Path

from .models import Config, StationConfig


def load_config(
    data_dir: Path | str = "data", config_path: Path | str | None = None
) -> Config:
    """
    Load configuration from files.
    """
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    if config_path is None:
        resolved_config_path = data_dir / "config.json"
    else:
        resolved_config_path = Path(config_path)

    with open(resolved_config_path) as f:
        raw_config = json.load(f)

    stations_config = StationConfig(**raw_config)

    config = Config(data_dir=data_dir, stations=stations_config)

    return config
