import pytest
from unittest.mock import patch, MagicMock
from src.user_password_checker import is_password_set


@pytest.fixture
def mock_db_url(monkeypatch):
    monkeypatch.setenv("SUPABASE_POSTGRES_CONNECTION_STRING", "mock_db_url")


@pytest.fixture
def mock_email(monkeypatch):
    monkeypatch.setenv("FIRST_EMAIL", "test@example.com")


@patch("psycopg2.connect")
def test_is_password_set_true(mock_connect, mock_db_url, mock_email):
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = ("hashed_password",)
    mock_connect.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = (
        mock_cursor
    )

    assert is_password_set(db_url="mock_db_url", email="test@example.com") == 'password set'
    mock_cursor.execute.assert_called_once_with(
        "SELECT encrypted_password FROM auth.users WHERE email = %s",
        ("test@example.com",),
    )


@patch("psycopg2.connect")
def test_is_password_set_false(mock_connect, mock_db_url, mock_email):
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = (None,)
    mock_connect.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = (
        mock_cursor
    )

    assert is_password_set(db_url="mock_db_url", email="test@example.com") == 'password not set'
    mock_cursor.execute.assert_called_once_with(
        "SELECT encrypted_password FROM auth.users WHERE email = %s",
        ("test@example.com",),
    )

@patch("psycopg2.connect")
def test_is_password_set_user_not_found(mock_connect, mock_db_url, mock_email):
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = None
    with pytest.raises(Exception) as exc_info:
        mock_connect.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = (
            mock_cursor
        )

        is_password_set(db_url="mock_db_url", email="june.may@test.com")
        mock_cursor.execute.assert_called_once_with(
            "SELECT encrypted_password FROM auth.users WHERE email = %s",
            ("june.may@test.com" ,),
        )

@patch("psycopg2.connect")
def test_is_password_set_exception(mock_connect, mock_db_url, mock_email):
    mock_connect.side_effect = Exception("Database connection error")

    with pytest.raises(Exception) as exc_info:
        is_password_set(db_url="mock_db_url", email="test@example.com")
    assert str(exc_info.value) == "Database connection error"
