import json
import logging
from typing import Optional, Tuple

import yaml
from supacrud import Supabase
from tenacity import retry

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def get_retry_config() -> dict:
    """Open config.yml and return the retry configuration."""
    with open("config.yml", encoding="utf-8", mode="r") as f:
        config = yaml.safe_load(f)
    return config["retry"]


def write_failed_invite(supabase_client: Supabase, payload: dict, error: str) -> bool:
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
        supabase_client.create(
            url="rest/v1/failed_invites",
            data={"email": email, "payload": payload, "error": error},
        )
        logger.info("Wrote failed invite to `failed_invites` table: %s", email)
        return True
    except Exception as error:
        logger.exception(
            "Error writing failed invite %s to `failed_invites` table: %s",
            payload,
            error,
        )
        return False


retry_config = get_retry_config()


@retry(**retry_config)
def failed_invite(supabase_client: Supabase, payload: dict, error: str) -> None:
    """
    Handle a failed invite.
    Args:
        supabase_client: Supabase
        payload: dict
        error: str
    Returns:
        None
    """
    write_failed_invite(supabase_client, payload, error)


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
    if not "redirect_to" in payload:  # if survey add the job id
        missing_values.append("redirect_to")
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
