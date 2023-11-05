# Path: tests/test_main.py
import pytest
from unittest.mock import Mock, patch
from flask import Request
from main import main
from src.user_service import UserService
from src.utils import validate_request, write_failed_invite


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
def mock_user_service():
    return Mock(spec=UserService)


@pytest.fixture
def sample_config():
    return {
        "supabase_url": "http://example.com",
        "anon_key": "anon_key",
        "supabase_key": "service_role_key",
        "redirect_to": "http://example.com",
    }


@patch("main.validate_request")
@patch("main.UserService")
@patch("main.Supabase")
def test_main_success(
    mock_supabase, mock_user_service, mock_validate_request, mock_request, sample_config
):
    mock_validate_request.return_value = (True, mock_request.get_json())
    mock_user_service.return_value.invite_user_with_retry.return_value = None
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
@patch("main.invite_user_with_retry")
@patch("main.write_failed_invite")
@patch("main.Supabase")
def test_main_failed_invite(
    mock_supabase,
    mock_write_failed_invite,
    mock_invite_user_with_retry,
    mock_user_service,
    mock_validate_request,
    mock_request,
    sample_config,
):
    mock_validate_request.return_value = (True, mock_request.get_json())
    mock_invite_user_with_retry.return_value = "test@example.com"
    response = main(mock_request)
    mock_write_failed_invite.assert_called_once()  # Now this should pass
    assert response.status == "500 INTERNAL SERVER ERROR"
