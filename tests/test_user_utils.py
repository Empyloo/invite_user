# Path: tests/test_user_utils.py
import pytest
from unittest.mock import Mock, patch

from src.user_service import UserService
from src.user_utils import invite_user


@pytest.fixture
def mock_user_service():
    return Mock(spec=UserService)


@pytest.fixture
def sample_payload():
    return {"email": "test@example.com", "redirect_to": "/survey"}


@pytest.fixture
def sample_config():
    return {"redirect_url_base": "http://example.com", "db_url": "http://example.com"}


@patch("src.get_link_type.is_password_set")
@patch("src.user_utils.generate_link_type")
@patch("src.user_service.UserService.generate_and_send_user_link")
def test_invite_user_success(
    mock_user_service,
    mock_generate_link_type,
    mock_is_password_set,
    sample_payload,
    sample_config,
):
    # Setup mocks
    mock_generate_link_type.return_value = "magiclink"
    mock_is_password_set.return_value = True
    mock_response = Mock(status_code=200)
    mock_user_service.return_value.generate_and_send_user_link.return_value = (
        mock_response
    )

    result = invite_user(mock_user_service(), sample_config, sample_payload)
    sample_payload["email"] = "test@example.com"

    assert result is None
    mock_is_password_set.assert_called_once_with(
        sample_config["db_url"], sample_payload["email"]
    )
    mock_generate_link_type.assert_called_once_with(sample_payload)
    mock_user_service.return_value.generate_and_send_user_link.assert_called_once_with(
        email=sample_payload["email"], link_type="magiclink"
    )


@patch("src.user_utils.generate_link_type")
def test_invite_user_failure(
    mock_generate_link_type, mock_user_service, sample_payload, sample_config
):
    mock_generate_link_type.return_value = "magiclink"
    mock_user_service.generate_and_send_user_link.side_effect = Exception("Error")
    assert (
        invite_user(mock_user_service, sample_config, sample_payload) == sample_payload
    )


@patch("src.user_utils.generate_link_type")
def test_invite_user_exception(
    mock_generate_link_type, mock_user_service, sample_payload, sample_config
):
    mock_generate_link_type.return_value = "magiclink"
    mock_user_service.generate_and_send_user_link.side_effect = Exception("Error")
    assert (
        invite_user(mock_user_service, sample_config, sample_payload) == sample_payload
    )
