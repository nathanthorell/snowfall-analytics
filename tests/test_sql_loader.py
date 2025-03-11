from pathlib import Path

import pytest

from snowfall_analytics.sql_loader import SQLLoader


@pytest.fixture
def sql_dir(tmp_path: Path) -> Path:
    """Create a temporary directory with test SQL files"""
    sql_dir = tmp_path / "sql"
    sql_dir.mkdir()

    # Create test SQL files
    schema_dir = sql_dir / "schema"
    schema_dir.mkdir()
    (schema_dir / "test_table.sql").write_text(
        "CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT);"
    )

    queries_dir = sql_dir / "queries"
    queries_dir.mkdir()
    (queries_dir / "insert_test.sql").write_text(
        "INSERT INTO test_table (id, name) VALUES (?, ?);"
    )

    return sql_dir


@pytest.fixture
def sql_loader(sql_dir: Path) -> SQLLoader:
    """Create SQLLoader instance with test directory"""
    return SQLLoader(sql_dir)


def test_get_query_success(sql_loader: SQLLoader) -> None:
    """Test successful query loading"""
    # Test loading schema file
    schema_query = sql_loader.get_query("schema/test_table")
    assert "CREATE TABLE test_table" in schema_query
    assert "id INTEGER PRIMARY KEY" in schema_query

    # Test loading query file
    insert_query = sql_loader.get_query("queries/insert_test")
    assert "INSERT INTO test_table" in insert_query
    assert "VALUES (?, ?)" in insert_query


def test_get_query_caching(sql_loader: SQLLoader, sql_dir: Path) -> None:
    """Test that queries are properly cached"""
    # Load query first time
    query1 = sql_loader.get_query("schema/test_table")

    # Modify file content
    (sql_dir / "schema" / "test_table.sql").write_text("MODIFIED CONTENT")

    # Load query again to get cached version
    query2 = sql_loader.get_query("schema/test_table")

    assert query1 == query2
    assert "CREATE TABLE" in query2  # Original content
    assert "MODIFIED CONTENT" not in query2  # Not updated content


def test_get_query_nonexistent(sql_loader: SQLLoader) -> None:
    """Test error handling for nonexistent SQL files"""
    with pytest.raises(FileNotFoundError) as exc_info:
        sql_loader.get_query("nonexistent/query")

    assert "SQL file not found" in str(exc_info.value)


def test_sql_loader_invalid_dir() -> None:
    """Test error handling for invalid SQL directory path"""
    loader = SQLLoader(Path("/nonexistent/directory"))
    with pytest.raises(FileNotFoundError):
        loader.get_query("any_query")
