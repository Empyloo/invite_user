# Path: tests/test_user_utils.py
import pytest
from unittest.mock import Mock, patch

from src.user_service import UserService
from src.user_utils import invite_user, invite_user_with_retry


@pytest.fixture
def mock_user_service():
    return Mock(spec=UserService)


@pytest.fixture
def sample_payload():
    return {"email": "test@example.com", "redirect_to": "/survey"}


@pytest.fixture
def sample_config():
    return {"redirect_url_base": "http://example.com"}


# Test cases for invite_user
@patch("src.user_utils.generate_link_type")
def test_invite_user_success(
    mock_generate_link_type, mock_user_service, sample_payload, sample_config
):
    mock_generate_link_type.return_value = "magiclink"
    mock_user_service.return_value.generate_and_send_user_link.return_value = Mock(status_code=200)
    assert invite_user(mock_user_service, sample_config, sample_payload) is None


@patch("src.user_utils.generate_link_type")
def test_invite_user_failure(
    mock_generate_link_type, mock_user_service, sample_payload, sample_config
):
    mock_generate_link_type.return_value = "magiclink"
    mock_user_service.generate_and_send_user_link.side_effect = Exception("Error")
    assert (
        invite_user(mock_user_service, sample_config, sample_payload) == sample_payload
    )


@patch("src.user_utils.invite_user")
def test_invite_user_with_retry_success(
    mock_invite_user, mock_user_service, sample_payload, sample_config
):
    mock_invite_user.return_value = None
    assert (
        invite_user_with_retry(mock_user_service, sample_config, sample_payload) is None
    )


@patch("src.user_utils.invite_user")
def test_invite_user_with_retry_failure(
    mock_invite_user, mock_user_service, sample_payload, sample_config
):
    mock_invite_user.return_value = "test@example.com"
    assert (
        invite_user_with_retry(mock_user_service, sample_config, sample_payload)
        == "test@example.com"
    )


@patch("src.user_utils.invite_user")
def test_invite_user_with_retry_exception(
    mock_invite_user, mock_user_service, sample_payload, sample_config
):
    mock_invite_user.side_effect = Exception("Error")
    with pytest.raises(Exception) as e:
        invite_user_with_retry(mock_user_service, sample_config, sample_payload)
    assert str(e.value) == "Error"
