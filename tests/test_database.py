"""Tests for the database module."""

import pytest

from agenticmcp.database import DatabaseManager


@pytest.mark.asyncio
async def test_sanitize_identifier() -> None:
    """Test SQL identifier sanitization."""
    db = DatabaseManager()

    # Valid identifiers
    assert db.sanitize_identifier("users") == '"users"'
    assert db.sanitize_identifier("user_id") == '"user_id"'
    assert db.sanitize_identifier("table-name") == '"table-name"'

    # Invalid identifiers
    with pytest.raises(ValueError):
        db.sanitize_identifier("users; DROP TABLE users; --")

    with pytest.raises(ValueError):
        db.sanitize_identifier("users' OR '1'='1")


def test_build_select_query() -> None:
    """Test SELECT query building."""
    db = DatabaseManager()

    # Simple query
    query, params = db.build_select_query("users")
    assert query == 'SELECT * FROM "users"'
    assert params == []

    # With columns
    query, params = db.build_select_query("users", columns=["id", "name"])
    assert query == 'SELECT "id", "name" FROM "users"'
    assert params == []

    # With WHERE
    query, params = db.build_select_query("users", where={"id": 1})
    assert query == 'SELECT * FROM "users" WHERE "id" = $1'
    assert params == [1]

    # With multiple WHERE conditions
    query, params = db.build_select_query(
        "users",
        where={"id": 1, "status": "active"}
    )
    assert 'WHERE "id" = $1' in query
    assert '"status" = $2' in query
    assert params == [1, "active"]

    # With ORDER BY
    query, params = db.build_select_query("users", order_by="created_at")
    assert query == 'SELECT * FROM "users" ORDER BY "created_at"'
    assert params == []

    # With LIMIT
    query, params = db.build_select_query("users", limit=10)
    assert query == 'SELECT * FROM "users" OFFSET $1 LIMIT $2'
    assert params == [0, 10]


def test_build_insert_query() -> None:
    """Test INSERT query building."""
    db = DatabaseManager()

    query, params = db.build_insert_query(
        "users",
        data={"name": "Alice", "email": "alice@example.com"}
    )
    assert query == 'INSERT INTO "users" ("name", "email") VALUES ($1, $2)'
    assert params == ["Alice", "alice@example.com"]

    # With RETURNING
    query, params = db.build_insert_query(
        "users",
        data={"name": "Bob"},
        returning="id"
    )
    assert query == 'INSERT INTO "users" ("name") VALUES ($1) RETURNING "id"'


def test_build_update_query() -> None:
    """Test UPDATE query building."""
    db = DatabaseManager()

    query, params = db.build_update_query(
        "users",
        data={"name": "Alice Updated"},
        where={"id": 1}
    )
    assert query == 'UPDATE "users" SET "name" = $1 WHERE "id" = $2'
    assert params == ["Alice Updated", 1]

    # Multiple fields
    query, params = db.build_update_query(
        "users",
        data={"name": "Alice", "status": "active"},
        where={"id": 1}
    )
    assert '"name" = $1' in query
    assert '"status" = $2' in query
    assert '"id" = $3' in query
    assert params == ["Alice", "active", 1]


def test_build_delete_query() -> None:
    """Test DELETE query building."""
    db = DatabaseManager()

    query, params = db.build_delete_query("users", where={"id": 1})
    assert query == 'DELETE FROM "users" WHERE "id" = $1'
    assert params == [1]

    # Multiple conditions
    query, params = db.build_delete_query(
        "users",
        where={"id": 1, "status": "inactive"}
    )
    assert '"id" = $1' in query
    assert '"status" = $2' in query
    assert params == [1, "inactive"]
