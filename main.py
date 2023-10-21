import os
import json
import logging
from typing import List, Optional, Tuple
import dotenv
import functions_framework
import yaml
from flask import Response
from gotrue.types import User
from tenacity import retry, stop_after_attempt, wait_exponential
from supabase import Client, create_client
from src.user_service import UserService

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def load_config():
    with open("config.yml", encoding="utf-8", mode="r") as f:
        config = yaml.safe_load(f)
    return config


def get_retry_config():
    config = load_config()
    return config["retry"]


def get_redirect_url():
    config = load_config()
    return config["redirect_url"]


retry_config = get_retry_config()
REDIRECT_URL = get_redirect_url()


def write_failed_invite(supabase_client: Client, payload: dict, error: str) -> bool:
    """
    Write the email: text, payload: jsonb and error: text
    to `failed_invites` table.
    Args:
        supabase_client: supabase.Client
        payload: dict
        error: str
    Returns:
        bool: True if the insert operation is successful, False otherwise
    """
    try:
        email = payload.get("email")
        supabase_client.from_("failed_invites").insert(
            {"email": email, "payload": payload, "error": error}
        ).execute()
        logger.info("Wrote failed invite to `failed_invites` table: %s", email)
        return True
    except Exception as error:
        logger.exception(
            "Error writing failed invite %s to `failed_invites` table: %s",
            payload,
            error,
        )
        return False


@retry(**retry_config)
def failed_invite(supabase_client: Client, payload: dict, error: str) -> None:
    """
    Handle a failed invite.
    Args:
        supabase_client: supabase.Client
        payload: dict
        error: str
    Returns:
        None
    """
    write_failed_invite(supabase_client, payload, error)


def check_user_exists(supabase_client: Client, email: str) -> bool:
    """
    Check if a user with the given email already exists.
    Args:
        supabase_client: supabase.Client
        email: str
    Returns:
        bool
    """
    try:
        users: List[User] = supabase_client.auth.api.list_users()
        if email in [user.email for user in users]:
            logger.info("User %s already exists", email)
            return True
        logger.info("User %s does not exist", email)
        return False
    except Exception as error:
        logger.exception("Error checking if user %s exists: %s", email, error)
        raise error


def send_invite(supabase_client: Client, payload: dict) -> None:
    """
    Invite the user with the given email to join the company.
    Args:
        supabase_client: supabase.Client
        payload: dict
    Returns:
        None
    """
    try:
        email = payload.get("email")
        payload.pop("email")
        supabase_client.auth.api.invite_user_by_email(
            email=email, data=payload, redirect_to=REDIRECT_URL
        )
        logger.info("Invited user %s", email)
    except Exception as error:
        logger.exception("Error inviting user %s, %s, %s", email, payload, error)
        raise error


def invite_user(user_service: UserService, payload: dict) -> Optional[dict]:
    """
    Invite the given user to join the given company,
    return the payload if request fails.
    Args:
        user_service: UserService
        payload: dict
    Returns:
        dict or None
    """
    try:
        email = payload.get("email")
        payload.pop("email")
        response = user_service.invite_user_by_email(email, payload, REDIRECT_URL)
        print(response.json())
        if response.status_code == 422:
            response = user_service.generate_and_send_user_link(
                email, "recover", REDIRECT_URL
            )
    except Exception as error:
        payload["email"] = email
        logger.exception("Error inviting user payload %s: %s", payload, error)
        return payload
    return None


def invite_user_with_retry(supabase_client: Client, user_service: UserService, payload: dict) -> Optional[str]:
    """
    Invite the given user to join the given company,
    return the email if request fails.
    Args:
        supabase_client: supabase.Client
        user_service: UserService
        payload: dict
    Returns:
        str or None
    """
    failed_email = invite_user(user_service=user_service, payload=payload)
    if failed_email:
        write_failed_invite(supabase_client, payload, "Failed to invite user.")
    return failed_email


def create_supabase_client() -> Client:
    """
    Create a supabase client using the credentials stored in the environment.
    If the .env file exists, load the credentials from it.
    Returns:
        supabase.Client
    """
    if os.path.exists(".env"):
        dotenv.load_dotenv()
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SERVICE_ROLE_KEY")
    supabase_client = create_client(supabase_url, supabase_key)
    logger.info("Created supabase client")
    return supabase_client


def missing_payload_values(payload: dict):
    """Check if the payload is missing any values."""
    missing_values = []
    if not "email" in payload:
        missing_values.append("email")
    if not "company_id" in payload:
        missing_values.append("company_id")
    if not "company_name" in payload:
        missing_values.append("company_name")
    if not "role" in payload:
        missing_values.append("role")
    return missing_values


def validate_request(request) -> Tuple[bool, Optional[str | dict]]:
    """
    Validate the request and return a tuple indicating if the request is valid
    and an error message if the request is invalid.
    Args:
        request: flask.Request
    Returns:
        Tuple[bool, Optional[str]]
    """
    if request.method != "POST":
        return (False, "Invalid request method")
    payload = request.get_data().decode("utf-8")
    try:
        payload = json.loads(payload)
    except json.decoder.JSONDecodeError:
        logger.error("Invalid request: %s" % payload)
        return (False, "Invalid request, no payload")
    logger.debug("Payload: %s" % payload)
    if not payload:
        return (False, "Invalid request, no payload")
    missing_values = missing_payload_values(payload)
    if missing_values:
        logger.error("Invalid request, missing values: %s", missing_values)
        return (False, f"Invalid request, missing values: {missing_values}")
    return (True, payload)


@functions_framework.http
def main(request):
    """
    Cloud Function entry point, http post request with json payload,
    containing the email and role of the user to invite a user to join.
    Args:
        request: flask.Request
    Returns:
        flask.Response
    """
    logger.info("Starting invite user function")
    is_valid, payload = validate_request(request)
    if not is_valid:
        logger.error(payload)
        return Response(payload, status=400)

    supabase_client = create_supabase_client()
    user_service = UserService(
        base_url=os.getenv("SUPABASE_URL"),
        api_key=os.getenv("SERVICE_ROLE_KEY"),
    )
    failed_email = invite_user_with_retry(supabase_client, user_service, payload)
    if failed_email:
        return Response(f"Failed to invite user: {failed_email}", status=500)
    return Response("Success", status=200)
