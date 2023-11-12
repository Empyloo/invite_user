import logging
from typing import Optional

from src.get_link_type import generate_link_type, resolve_link_type

from src.user_service import UserService

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def invite_user(
    user_service: UserService, config: dict, payload: dict
) -> Optional[dict]:
    """
    Invite a user to join a company, or participate in a survey/review.

    Args:
        user_service: UserService
        config: dict
        payload: dict
    Returns:
        dict or None
    """
    try:
        email = payload.get("email")
        payload.pop("email")
        payload["redirect_to"] = config["redirect_url_base"] + payload["redirect_to"]

        generated_link_type = generate_link_type(payload)
        link_type = resolve_link_type(config["db_url"], email, generated_link_type)

        response = user_service.generate_and_send_user_link(
            email=email, link_type=link_type
        )
        if response.status_code == 200:
            logger.info("Successfully invited user %s", email)
            return None
        else:
            logger.error(
                f"Failed to send {link_type} email to user {email}, status code: {response.status_code}"
            )
            return payload
    except Exception as error:
        payload["email"] = email
        logger.exception("Error inviting user payload %s: %s", payload, error)
        return payload
