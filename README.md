# snowfall-analytics

This project extracts snowfall data from NOAA's Climate Data API, processes it using DuckDB and dbt, and presents analytics through [Panel](https://panel.holoviz.org/) dashboards.
More documentation coming as the project develops.

## Setup

### Prerequisites

This project is designed with uv. Install uv:

- From a POSIX shell, run:

    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

- Or using Windows Powershell:

    ```powershell
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

Alternatively, see the [uv installation docs](https://docs.astral.sh/uv/getting-started/installation/) for other installation methods.

### Initial Setup

1. Clone the repository:

    ```bash
    git clone https://github.com/nathanthorell/snowfall-analytics.git
    cd snowfall-analytics
    ```

1. Create and install the development environment:

    ```bash
    uv sync
    ```

### Configuration

Edit `./data/config.json`

To find additional weather stations of interest use the [NCEI Station Locator](https://www.ncdc.noaa.gov/cdo-web/datatools/findstation)

## Common Commands

```bash
# Using uv (recommended)
uv run ruff check .           # Run code quality checks
uv run ruff format .          # Format code
uv run mypy .                 # Type checking
uv run pytest                 # Run tests
uv run snowfall_data_extract  # Run the data extraction tool

# Alternatively with make
make lint     # Run code quality checks
make format   # Format code
make test     # Run tests
```

## Project Structure

```text
snowfall-analytics/
├── snowfall_data_extract/           # Data extraction package
│   ├── cli.py                       # Command-line interface
│   ├── config/                      # Configuration management
│   │   ├── loader.py                # Config loading logic
│   │   └── models.py                # Config data models
│   ├── sql/                         # SQL files
│   │   ├── schema/                  # Database schema definitions
│   │   └── queries/                 # SQL queries for operations
│   ├── noaa.py                      # NOAA API client and models
│   ├── sql_loader.py                # loads dir of sql files
│   └── db.py                        # DuckDB operations
├── snowfall_dbt/                    # dbt transformations package
├── snowfall_panel/                  # Panel dashboards package
├── tests/                           # Test files
├── pyproject.toml                   # Python package configuration
└── Makefile                         # Build and development commands
```
