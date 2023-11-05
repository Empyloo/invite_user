import logging
from typing import List, Optional

from gotrue.types import User
from supabase import Client
from src.get_link_type import generate_link_type

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

        link_type = generate_link_type(payload)
        response = user_service.generate_and_send_user_link(
            email=email, link_type=link_type
        )
        if response.status_code == 200:
            logger.info("Successfully invited user %s", email)
            return None

        elif response.status_code == 422:
            logger.info("User %s already exists", email)
            recovery_response = user_service.generate_and_send_user_link(
                user_service, email, "recover"
            )
            if recovery_response.status_code == 200:
                logger.info("Successfully sent recovery email to user %s", email)
                return None
            else:
                logger.error("Failed to send recovery email to user %s", email)
                return payload
    except Exception as error:
        payload["email"] = email
        logger.exception("Error inviting user payload %s: %s", payload, error)
        return payload
    return None


def invite_user_with_retry(
    user_service: UserService, config: dict, payload: dict
) -> Optional[str]:
    """
    Invite a user to join a company, or participate in a survey/review.

    Args:
        user_service: UserService
        config: dict
        payload: dict
    Returns:
        str or None
    """
    failed_email = invite_user(
        user_service=user_service, config=config, payload=payload
    )
    return failed_email
