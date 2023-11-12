# Path: tests/test_main.py
import os
import pytest
from unittest.mock import Mock, patch
from flask import Request, Response
from main import main, load_config
from src.user_service import UserService
from src.utils import validate_request, write_failed_invite


@pytest.fixture(autouse=True)
def mock_env_variables(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "mock_supabase_url")
    monkeypatch.setenv("ANON_KEY", "mock_anon_key")
    monkeypatch.setenv("SERVICE_ROLE_KEY", "mock_service_role_key")


@pytest.fixture
def mock_supabase():
    with patch("main.Supabase") as mock_supabase_class:
        mock_supabase_instance = mock_supabase_class.return_value
        yield mock_supabase_instance


@pytest.fixture
def mock_user_service(mock_supabase):
    with patch("main.UserService") as mock_user_service_class:
        mock_user_service_instance = mock_user_service_class.return_value
        mock_user_service_class.return_value = mock_user_service_instance
        yield mock_user_service_instance


@pytest.fixture
def mock_request():
    request = Mock(spec=Request)
    request.get_json.return_value = {
        "email": "test@example.com",
        "role": "user",
        "redirect_to": "/survey",
    }
    return request


@pytest.fixture
def mock_validate_request():
    with patch("main.validate_request") as mock_validate_request_func:
        mock_validate_request_func.return_value = (
            True,
            {"email": "test@example.com", "role": "admin", "redirect_to": "/survey"},
        )
        yield mock_validate_request_func


@pytest.fixture
def mock_write_failed_invite(mock_supabase):
    with patch("main.write_failed_invite") as mock_write_failed_invite_func:
        yield mock_write_failed_invite_func


@pytest.fixture
def sample_config():
    return {
        "supabase_url": "http://example.com",
        "anon_key": "anon_key",
        "supabase_key": "service_role_key",
        "redirect_url_base": "http://example.com",
    }


@patch("src.get_link_type.is_password_set")
@patch("main.validate_request")
@patch("main.UserService")
@patch("main.Supabase")
def test_main_success(
    mock_supabase,
    mock_user_service,
    mock_validate_request,
    mock_is_password_set,
    mock_request,
    sample_config,
):
    mock_validate_request.return_value = (True, mock_request.get_json())
    mock_is_password_set.return_value = True

    mock_user_service.return_value.invite_user.return_value = None
    mock_user_service.return_value.generate_and_send_user_link.return_value = Mock(
        status_code=200
    )

    response = main(mock_request)
    assert response.status == "200 OK"


@patch("main.validate_request")
@patch("main.UserService")
@patch("main.Supabase")
def test_main_invalid_request(
    mock_supabase, mock_user_service, mock_validate_request, mock_request, sample_config
):
    mock_validate_request.return_value = (False, "Invalid request")
    response = main(mock_request)
    assert response.status == "400 BAD REQUEST"


@patch("main.validate_request")
@patch("main.UserService")
@patch("main.invite_user")
@patch("main.write_failed_invite")
@patch("main.Supabase")
def test_main_failed_invite(
    mock_supabase,
    mock_write_failed_invite,
    mock_invite_user,
    mock_user_service,
    mock_validate_request,
    mock_request,
    sample_config,
):
    mock_validate_request.return_value = (True, mock_request.get_json())
    mock_invite_user.return_value = "test@example.com"
    response = main(mock_request)
    mock_write_failed_invite.assert_called_once()  # Now this should pass
    assert response.status == "500 INTERNAL SERVER ERROR"


@patch("main.load_config", return_value=sample_config)
@patch("main.Supabase")
@patch("main.UserService")
@patch("main.validate_request")
@patch("main.invite_user")
@patch("main.write_failed_invite")
def test_main_failed_invites(
    mock_write_failed_invite,
    mock_invite_user,
    mock_validate_request,
    mock_user_service,
    mock_supabase,
    mock_load_config,
    mock_request,
):
    mock_validate_request.return_value = (True, mock_request.get_json())
    mock_invite_user.return_value = "e@email.com"
    response = main(mock_request)
    mock_write_failed_invite.assert_called_once()
    assert response.status == "500 INTERNAL SERVER ERROR"
