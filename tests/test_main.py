import os
import json
import pytest
import main
from unittest import mock
from supabase import Client
from gotrue.types import User
from tenacity import retry, stop_after_attempt, wait_exponential

from src.user_service import UserService


@pytest.fixture
def mock_user_service():
    return mock.Mock(spec=UserService)


@pytest.fixture(scope="function")
def config_file(tmpdir):
    config = tmpdir.join("config.yml")
    config.write(
        """
        retry:
          reraise: true
          stop:
            after_attempt: 3
          wait:
            exponential:
              multiplier: 1
              max: 6
        """
    )
    return config


def test_load_config(config_file):
    current_dir = os.getcwd()
    os.chdir(config_file.dirname)
    config = main.load_config()
    assert config == {
        "retry": {
            "reraise": True,
            "stop": {"after_attempt": 3},
            "wait": {"exponential": {"multiplier": 1, "max": 6}},
        }
    }
    os.chdir(current_dir)


def test_get_retry_config(config_file):
    os.environ["CONFIG_PATH"] = str(config_file)
    retry_config = main.get_retry_config()
    assert retry_config == {
        "reraise": True,
        "stop": {"after_attempt": 3},
        "wait": {"exponential": {"multiplier": 1, "max": 6}},
    }


def test_write_failed_invite():
    mock_client = mock.Mock(spec=Client)
    mock_client.from_("failed_invites").insert().execute.return_value = []
    payload = {"email": "test@example.com", "custom_field": "value"}
    error = "Error sending invite"
    main.write_failed_invite(mock_client, payload, error)
    mock_client.from_("failed_invites").insert.assert_called_with(
        {"email": "test@example.com", "payload": payload, "error": error}
    )


def test_write_failed_invite_twice(mocker):
    payload = {"email": "test@example.com", "name": "Test User"}
    error = "Test error message"
    supabase_client = mocker.Mock(spec=Client)
    supabase_client.from_(
        "failed_invites"
    ).insert().return_value.execute.return_value = {"id": 1}
    result = main.write_failed_invite(supabase_client, payload, error)
    supabase_client.from_("failed_invites").insert.assert_called_with(
        {"email": "test@example.com", "payload": payload, "error": error}
    )
    assert result is True


def test_write_failed_invite_success(mocker):
    payload = {"email": "test@example.com", "name": "Test User"}
    error = "Test error message"
    supabase_client = mocker.Mock(spec=Client)
    supabase_client.from_("failed_invites").insert().execute.return_value = True
    result = main.write_failed_invite(supabase_client, payload, error)
    supabase_client.from_("failed_invites").insert.assert_called_with(
        {"email": "test@example.com", "payload": payload, "error": error}
    )
    assert result == True


def test_write_failed_invite_failure(mocker):
    payload = {"email": "test@example.com", "name": "Test User"}
    error = "Test error message"
    supabase_client = mocker.Mock(spec=Client)
    supabase_client.from_("failed_invites").insert.side_effect = Exception(
        "Test exception"
    )
    result = main.write_failed_invite(supabase_client, payload, error)
    supabase_client.from_("failed_invites").insert.assert_called_with(
        {"email": "test@example.com", "payload": payload, "error": error}
    )
    assert result == False


def test_failed_invite_success(mocker):
    payload = {"email": "test@example.com", "name": "Test User"}
    error = "Test error message"
    supabase_client = mocker.Mock(spec=Client)
    mocker.patch.object(main, "write_failed_invite", return_value=True)
    result = main.failed_invite(supabase_client, payload, error)
    main.write_failed_invite.assert_called_with(supabase_client, payload, error)
    assert result is None


def test_check_user_exists(mocker):
    supabase_client = mocker.Mock(spec=Client)
    supabase_client.auth = mocker.Mock()
    supabase_client.auth.api = mocker.Mock()
    supabase_client.auth.api.list_users.return_value = [
        User(
            id="123e4567-e89b-12d3-a456-426655440000",
            email="user1@example.com",
            app_metadata={},
            aud="",
            created_at="2022-12-29T00:00:00Z",
            user_metadata={},
        ),
        User(
            id="123e4567-e89b-12d3-a456-426655440000",
            email="user2@example.com",
            app_metadata={},
            aud="",
            created_at="2022-12-29T00:00:00Z",
            user_metadata={},
        ),
    ]
    assert main.check_user_exists(supabase_client, "user2@example.com") is True


def test_check_user_exists_empty_return(mocker):
    supabase_client = mocker.Mock(spec=Client)
    supabase_client.auth = mocker.Mock()
    supabase_client.auth.api = mocker.Mock()
    supabase_client.auth.api.list_users.return_value = []
    assert main.check_user_exists(supabase_client, "user2@example.com") is False


def test_check_user_exists_exception(mocker):
    supabase_client = mocker.Mock(spec=Client)
    supabase_client.auth = mocker.Mock()
    supabase_client.auth.api = mocker.Mock()
    supabase_client.auth.api.list_users.side_effect = Exception("Test exception")
    with pytest.raises(Exception):
        main.check_user_exists(supabase_client, "user2@example.com")


@mock.patch("main.REDIRECT_URL", "https://example.com/invite")
def test_send_invite_success(mocker):
    payload = {
        "email": "user@example.com",
        "company_name": "Test Company",
        "company_id": "5fccbf1f-cc62-47b2-906b-98b861913e8d",
        "role": "member",
    }
    supabase_client = mocker.Mock(spec=Client)
    supabase_client.auth = mocker.Mock()
    supabase_client.auth.api = mocker.Mock()
    supabase_client.auth.api.invite_user_by_email.return_value = True
    main.send_invite(supabase_client, payload)
    supabase_client.auth.api.invite_user_by_email.assert_called_with(
        email="user@example.com",
        redirect_to="https://example.com/invite",
        data={
            "company_name": "Test Company",
            "company_id": "5fccbf1f-cc62-47b2-906b-98b861913e8d",
            "role": "member",
        },
    )


@mock.patch("main.REDIRECT_URL", "https://example.com/invite")
def test_send_invite_failure(mocker):
    payload = {
        "company_name": "Test Company",
        "company_id": "5fccbf1f-cc62-47b2-906b-98b861913e8d",
        "role": "member",
    }
    supabase_client = mocker.Mock(spec=Client)
    supabase_client.auth = mocker.Mock()
    supabase_client.auth.api = mocker.Mock()
    supabase_client.auth.api.invite_user_by_email.side_effect = Exception(
        "Test exception"
    )
    with pytest.raises(Exception):
        main.send_invite(supabase_client, payload)


@mock.patch("main.REDIRECT_URL", "https://example.com/invite")
@mock.patch("main.logger")
def test_invite_user_new_user(mock_logger, mock_user_service):
    payload = {
        "email": "user@example.com",
        "company_name": "Test Company",
        "company_id": "5fccbf1f-cc62-47b2-906b-98b861913e8d",
        "role": "member",
    }

    # Configure the mock response for invite_user_by_email
    mock_response = mock.Mock()
    mock_response.status_code = 422
    mock_user_service.invite_user_by_email.return_value = mock_response

    # Configure the mock response for generate_and_send_user_link
    mock_response_link = mock.Mock()
    mock_response_link.status_code = 200
    mock_user_service.generate_and_send_user_link.return_value = mock_response_link

    # Call the invite_user function with the mock UserService and payload
    assert main.invite_user(mock_user_service, payload) is None

    # Check if invite_user_by_email and generate_and_send_user_link were called with the correct arguments
    mock_user_service.invite_user_by_email.assert_called_once_with(
        "user@example.com", payload, "https://example.com/invite"
    )
    mock_user_service.generate_and_send_user_link.assert_called_once_with(
        "user@example.com", "recover", "https://example.com/invite"
    )


@mock.patch("main.REDIRECT_URL", "https://example.com/invite")
@mock.patch("main.logger")
def test_invite_user_user_exists(mock_logger, mock_user_service):
    payload = {
        "email": "user@example.com",
        "company_name": "Test Company",
        "company_id": "5fccbf1f-cc62-47b2-906b-98b861913e8d",
        "role": "member",
    }

    # Configure the mock response for invite_user_by_email
    mock_response = mock.Mock()
    mock_response.status_code = 200
    mock_user_service.invite_user_by_email.return_value = mock_response

    # Call the invite_user function with the mock UserService and payload
    assert main.invite_user(mock_user_service, payload) is None

    # Check if invite_user_by_email was called with the correct arguments
    mock_user_service.invite_user_by_email.assert_called_once_with(
        "user@example.com", payload, "https://example.com/invite"
    )


@mock.patch("main.REDIRECT_URL", "https://example.com/invite")
@mock.patch("main.check_user_exists", return_value=True)
@mock.patch("main.send_invite")
def test_invite_user_send_invite_exception(
    mock_send_invite, mock_check_user_exists, mocker
):
    payload = {
        "email": "user@example.com",
        "company_name": "Test Company",
        "company_id": "5fccbf1f-cc62-47b2-906b-98b861913e8d",
        "role": "member",
    }
    supabase_client = mocker.Mock(spec=Client)
    supabase_client.auth = mocker.Mock()
    supabase_client.auth.api = mocker.Mock()
    mock_check_user_exists.return_value = False
    mock_send_invite.side_effect = Exception("Test exception")
    result = main.invite_user(supabase_client, payload)
    assert result == payload



@mock.patch("main.invite_user", return_value=None)
@mock.patch("main.write_failed_invite")
def test_invite_user_with_retry_success(
    mock_write_failed_invites, mock_invite_user, mocker, mock_user_service
):
    payload = {
        "email": "user@example.com",
        "company_name": "Test Company",
        "company_id": "5fccbf1f-cc62-47b2-906b-98b861913e8d",
        "role": "member",
    }
    supabase_client = mocker.Mock(spec=Client)
    mock_invite_user.return_value = None
    assert main.invite_user_with_retry(supabase_client, mock_user_service, payload) is None


@mock.patch("main.invite_user", return_value=None)
@mock.patch("main.write_failed_invite")
def test_invite_user_with_retry_failure(
    mock_write_failed_invites, mock_invite_user, mocker
):
    payload = {
        "email": "user@example.com",
        "company_name": "Test Company",
        "company_id": "5fccbf1f-cc62-47b2-906b-98b861913e8d",
        "role": "member",
    }
    supabase_client = mocker.Mock(spec=Client)
    mock_invite_user.return_value = payload
    assert mock_write_failed_invites.called_once_with(
        supabase_client, payload, "Failed to invite user."
    )


def test_create_supabase_client(mocker):
    dotenv_mock = mocker.patch("dotenv.load_dotenv")
    os_mock = mocker.patch("os.path.exists")
    os_mock.return_value = True
    os.environ["SUPABASE_URL"] = "test_url"
    os.environ["SUPABASE_KEY"] = "test_key"
    mock_supabase_client = mocker.Mock(spec=Client)
    mocker.patch("main.create_client", return_value=mock_supabase_client)
    assert main.create_supabase_client() == mock_supabase_client


def test_missing_payload_values_success():
    payload = {
        "email": "user@example.com",
        "company_name": "Test Company",
        "company_id": "5fccbf1f-cc62-47b2-906b-98b861913e8d",
        "role": "member",
    }
    assert main.missing_payload_values(payload) == []


def test_missing_payload_values_missing_email():
    payload = {
        "company_name": "Test Company",
        "company_id": "5fccbf1f-cc62-47b2-906b-98b861913e8d",
        "role": "member",
    }
    assert main.missing_payload_values(payload) == ["email"]


def test_missing_payload_values_missing_company_id():
    payload = {
        "email": "user@example.com",
        "company_name": "Test Company",
        "role": "member",
    }
    assert main.missing_payload_values(payload) == ["company_id"]


def test_missing_payload_values_missing_company_name():
    payload = {
        "email": "user@example.com",
        "company_id": "5fccbf1f-cc62-47b2-906b-98b861913e8d",
        "role": "member",
    }
    assert main.missing_payload_values(payload) == ["company_name"]


def test_missing_payload_values_missing_role():
    payload = {
        "email": "user@example.com",
        "company_name": "Test Company",
        "company_id": "5fccbf1f-cc62-47b2-906b-98b861913e8d",
    }
    assert main.missing_payload_values(payload) == ["role"]


def test_validate_request_with_valid_payload(monkeypatch):
    monkeypatch.setattr("main.missing_payload_values", lambda payload: [])

    payload = {
        "email": "test@example.com",
        "company_id": 1,
        "company_name": "Test Company",
        "role": "user",
    }
    converted_payload = json.dumps(payload).encode()

    request = mock.MagicMock()
    request.method = "POST"
    request.get_data.return_value = converted_payload

    result = main.validate_request(request)
    assert result == (
        True,
        {
            "email": "test@example.com",
            "company_id": 1,
            "company_name": "Test Company",
            "role": "user",
        },
    )


def test_validate_request_with_invalid_method(monkeypatch):
    monkeypatch.setattr("main.missing_payload_values", lambda payload: [])

    request = mock.MagicMock()
    request.method = "GET"

    result = main.validate_request(request)
    assert result == (False, "Invalid request method")


def test_validate_request_with_empty_payload(monkeypatch):
    monkeypatch.setattr("main.missing_payload_values", lambda payload: [])

    request = mock.MagicMock()
    request.method = "POST"
    request.get_data.return_value = b""

    result = main.validate_request(request)
    assert result == (False, "Invalid request, no payload")


def test_validate_request_with_missing_payload_values(monkeypatch):
    monkeypatch.setattr(
        "main.missing_payload_values", lambda payload: ["company_id", "company_name"]
    )

    payload = {
        "email": "test@example.com",
        "role": "user",
    }
    converted_payload = json.dumps(payload).encode()

    request = mock.MagicMock()
    request.method = "POST"
    request.get_data.return_value = converted_payload

    result = main.validate_request(request)
    assert result == (
        False,
        "Invalid request, missing values: ['company_id', 'company_name']",
    )


def test_main_success(mocker):
    request = mocker.Mock()
    request.method = "POST"
    request.get_json.return_value = {
        "email": "test_user@work.com",
        "company_name": "Test Company",
        "company_id": "5fccbf1f-cc62-47b2-906b-98b861913e8d",
        "role": "member",
    }
    mock_validate_request = mocker.patch("main.validate_request")
    mock_validate_request.return_value = (True, None)
    mock_create_supabase_client = mocker.patch("main.create_supabase_client")
    mock_invite_user_with_retry = mocker.patch("main.invite_user_with_retry")
    mock_invite_user_with_retry.return_value = None
    response = main.main(request)
    assert response.status_code == 200
    assert response.data == b"Success"


def test_main_invalid_request(mocker):
    request = mocker.Mock()
    request.method = "POST"
    request.get_json.return_value = {
        "email": "test_user@work.com",
        "company_name": "Test Company",
        "company_id": "5fccbf1f-cc62-47b2-906b-98b861913e8d",
        "role": "member",
    }
    mock_validate_request = mocker.patch("main.validate_request")
    mock_validate_request.return_value = (False, "Invalid request")
    response = main.main(request)
    assert response.status_code == 400
    assert response.data == b"Invalid request"


def test_main_invite_user_failed(mocker):
    request = mocker.Mock()
    request.method = "POST"
    request.get_json.return_value = {
        "email": "test_user@work.com",
        "company_name": "Test Company",
        "company_id": "5fccbf1f-cc62-47b2-906b-98b861913e8d",
        "role": "member",
    }
    mock_validate_request = mocker.patch("main.validate_request")
    mock_validate_request.return_value = (True, None)
    mock_create_supabase_client = mocker.patch("main.create_supabase_client")
    mock_invite_user_with_retry = mocker.patch("main.invite_user_with_retry")
    mock_invite_user_with_retry.return_value = "test_user@work.com"
    response = main.main(request)
    assert response.status_code == 500
    assert response.data == b"Failed to invite user: test_user@work.com"
