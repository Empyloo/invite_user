import pytest
from unittest.mock import patch, MagicMock
from src.user_service import UserService
from supacrud import Supabase, ResponseType


config = {"supabase_url": "https://example.com", "supabase_service_key": "example_key"}


mock_supabase = MagicMock(spec=Supabase)


user_service = UserService(mock_supabase, config)


ExpectedResponseType = ResponseType


def test_invite_user_by_email():
    mock_supabase.create.return_value = ExpectedResponseType
    assert user_service.invite_user_by_email("test@example.com") == ExpectedResponseType
    assert (
        user_service.invite_user_by_email("test2@example.com", {"key": "value"})
        == ExpectedResponseType
    )
    assert (
        user_service.invite_user_by_email("test3@example.com", None)
        == ExpectedResponseType
    )


def test_generate_and_send_user_link():
    mock_supabase.create.return_value = ExpectedResponseType
    assert (
        user_service.generate_and_send_user_link("test@example.com")
        == ExpectedResponseType
    )
    assert (
        user_service.generate_and_send_user_link("test2@example.com", "magiclink")
        == ExpectedResponseType
    )
    assert (
        user_service.generate_and_send_user_link("test3@example.com", "otherlink")
        == ExpectedResponseType
    )


def test_update_user():
    mock_supabase.update.return_value = ExpectedResponseType
    assert (
        user_service.update_user("token1", "test@example.com") == ExpectedResponseType
    )
    assert (
        user_service.update_user("token2", "test2@example.com", "password")
        == ExpectedResponseType
    )
    assert (
        user_service.update_user(
            "token3", "test3@example.com", "password", {"key": "value"}
        )
        == ExpectedResponseType
    )


def test_generate_invite_link():
    mock_supabase.create.return_value = ExpectedResponseType
    assert user_service.generate_invite_link("test@example.com") == ExpectedResponseType
    assert (
        user_service.generate_invite_link("test2@example.com", {"key": "value"})
        == ExpectedResponseType
    )
    assert (
        user_service.generate_invite_link(
            "test3@example.com", {"key": "value"}, "http://example.com", "invite"
        )
        == ExpectedResponseType
    )
