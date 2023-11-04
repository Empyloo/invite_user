import pytest  # type: ignore
import httpx  # type: ignore
from httpx import Response
from src.user_service import UserService

# Replace these values with the actual base URL and API key of your Supabase instance.
BASE_URL = "https://your-instance.supabase.co"
API_KEY = "your-api-key"


def mock_response(status_code: int, content: str) -> Response:
    return Response(status_code=status_code, text=content)


def test_invite_user_by_email(mocker):
    email = "someone@email.com"
    data = {"key": "value"}

    # Mock httpx.post
    mocker.patch("httpx.post", return_value=mock_response(200, "OK"))

    user_service = UserService(BASE_URL, API_KEY)
    response = user_service.invite_user_by_email(email, data)

    assert response.status_code == 200
    assert response.text == "OK"


def test_generate_and_send_user_link(mocker):
    email = "someone@email.com"
    link_type = "magiclink"

    # Mock httpx.post
    mocker.patch("httpx.post", return_value=mock_response(200, "OK"))

    user_service = UserService(BASE_URL, API_KEY)
    response = user_service.generate_and_send_user_link(email, link_type)

    assert response.status_code == 200
    assert response.text == "OK"


def test_get_user(mocker):
    user_token = "user-token"

    # Mock httpx.get
    mocker.patch("httpx.get", return_value=mock_response(200, "OK"))

    user_service = UserService(BASE_URL, API_KEY)
    response = user_service.get_user(user_token)

    assert response.status_code == 200
    assert response.text == "OK"


def test_update_user(mocker):
    user_token = "user-token"
    email = "new-email@email.com"
    password = "new-password"
    data = {"key": "new-value"}

    # Mock httpx.put
    mocker.patch("httpx.put", return_value=mock_response(200, "OK"))

    user_service = UserService(BASE_URL, API_KEY)
    response = user_service.update_user(user_token, email, password, data)

    assert response.status_code == 200
    assert response.text == "OK"
