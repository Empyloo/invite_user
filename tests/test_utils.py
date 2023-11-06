# test_utils.py
import pytest
from unittest.mock import patch, Mock, mock_open
from src.utils import (
    get_retry_config,
    write_failed_invite,
    missing_payload_values,
    validate_request,
)


@patch(
    "builtins.open", new_callable=mock_open, read_data="retry: \n  wait: 2\n  stop: 10"
)
def test_get_retry_config(mock_open):
    expected_config = {"wait": 2, "stop": 10}
    assert get_retry_config() == expected_config


@patch("src.utils.Supabase.create")
def test_write_failed_invite(mock_client):
    mock_client.return_value = {"status_code": 200}
    payload = {"email": "test@example.com"}
    error = "Test error"
    assert write_failed_invite(mock_client, payload, error) == True


def test_missing_payload_values_all_present():
    payload = {
        "email": "test@example.com",
        "company_id": "123",
        "company_name": "Test Company",
        "role": "member",
        "redirect_to": "/path",
    }
    assert missing_payload_values(payload) == []


def test_missing_payload_values_some_missing():
    payload = {"email": "test@example.com", "company_id": "123", "role": "member"}
    assert missing_payload_values(payload) == ["company_name", "redirect_to"]


def test_missing_payload_values_all_missing():
    payload = {}
    assert missing_payload_values(payload) == [
        "email",
        "company_id",
        "company_name",
        "role",
        "redirect_to",
    ]


def test_validate_request_invalid_method():
    request = Mock()
    request.method = "GET"
    assert validate_request(request) == (False, "Invalid request method")


def test_validate_request_no_payload():
    request = Mock()
    request.method = "POST"
    request.get_data.return_value = b""
    assert validate_request(request) == (False, "Invalid request, no payload")


def test_validate_request_invalid_payload():
    request = Mock()
    request.method = "POST"
    request.get_data.return_value = b"invalid json"
    assert validate_request(request) == (False, "Invalid request, no payload")


def test_validate_request_missing_values():
    request = Mock()
    request.method = "POST"
    request.get_data.return_value = b'{"email": "test@example.com"}'
    assert validate_request(request) == (
        False,
        "Invalid request, missing values: ['company_id', 'company_name', 'role', 'redirect_to']",
    )


def test_validate_request_valid():
    request = Mock()
    request.method = "POST"
    request.get_data.return_value = b'{"email": "test@example.com", "company_id": "123", "company_name": "Test Company", "role": "member", "redirect_to": "/path"}'
    assert validate_request(request) == (
        True,
        {
            "email": "test@example.com",
            "company_id": "123",
            "company_name": "Test Company",
            "role": "member",
            "redirect_to": "/path",
        },
    )
