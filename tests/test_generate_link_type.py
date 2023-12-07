import pytest
from unittest.mock import patch, Mock
from src.get_link_type import generate_link_type, resolve_link_type


def test_generate_link_type_invite():
    payload = {"redirect_to": "/set-password"}
    assert generate_link_type(payload) == "invite"


def test_generate_link_type_magiclink():
    payload = {"redirect_to": "/survey"}
    assert generate_link_type(payload) == "magiclink"


def test_generate_link_type_recover():
    payload = {"redirect_to": "/reset-password"}
    assert generate_link_type(payload) == "recover"


def test_generate_link_type_invalid():
    payload = {"redirect_to": "/invalid"}
    with pytest.raises(ValueError):
        generate_link_type(payload)


@pytest.fixture
def mock_is_password_set():
    with patch("src.get_link_type.is_password_set") as mock:
        yield mock


def test_resolve_link_type_password_set(mock_is_password_set):
    mock_is_password_set.return_value = "password set"
    assert resolve_link_type("db_url", "test@example.com", "magiclink") == "magiclink"


def test_resolve_link_type_password_not_set(mock_is_password_set):
    mock_is_password_set.return_value = "password not set"
    assert resolve_link_type("db_url", "test@example.com", "magiclink") == "recover"


def test_resolve_link_type_user_not_found(mock_is_password_set):
    mock_is_password_set.side_effect = Exception("User not found")
    with pytest.raises(Exception):
        resolve_link_type("db_url", "test@example.com", "magiclink")


def test_resolve_link_type_password_set_invite(mock_is_password_set):
    mock_is_password_set.return_value = "password set"
    assert resolve_link_type("db_url", "test@example.com", "invite") == "recover"
