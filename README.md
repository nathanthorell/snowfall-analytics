# snowfall-analytics

This project extracts snowfall data from NOAA's Climate Data API, processes it using DuckDB and dbt, and presents analytics through [Panel](https://panel.holoviz.org/) dashboards.
More documentation coming as the project develops.

## Setup

### Prerequisites

- Python 3.12+
- Make

### Initial Setup

1. Clone the repository:

    ```bash
    git clone https://github.com/nathanthorell/snowfall-analytics.git
    cd snowfall-analytics
    ```

1. Create and install the development environment:

    ```bash
    make install
    source .venv/bin/activate
    ```

## Common Commands

```bash
make lint     # Run code quality checks
make format   # Format code
make test     # Run tests
make all      # Run format, lint, and test
```

## Project Structure

```text
snowfall-analytics/
├── src/
│   └── snowfall_analytics/
│       ├── cli.py           # Command-line interface
│       ├── config.py        # Configuration management
│       ├── noaa.py          # NOAA API client and models
│       ├── sql_loader.py    # loads dir of sql files
│       └── db.py            # DuckDB operations
├── tests/                   # Test files
├── dbt_snowfall/            # dbt transformations
├── dashboards/              # Panel dashboards
├── pyproject.toml           # Python package configuration
└── Makefile                 # Build and development commands
```
