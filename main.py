import os
import logging

import functions_framework
import dotenv
import yaml
from flask import Response
from supacrud import Supabase

from src.user_service import UserService
from src.user_utils import invite_user_with_retry
from src.utils import validate_request, write_failed_invite

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def load_config():
    with open("config.yml", encoding="utf-8", mode="r") as f:
        config = yaml.safe_load(f)
    return config


config = load_config()

dotenv.load_dotenv()
config["supabase_url"] = os.getenv("SUPABASE_URL")
config["anon_key"] = os.getenv("ANON_KEY")
config["supabase_key"] = os.getenv("SERVICE_ROLE_KEY")


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

    supabase_client = Supabase(
        base_url=config["supabase_url"],
        service_role_key=config["supabase_key"],
        anon_key=config["anon_key"],
    )
    user_service = UserService(
        client=supabase_client,
        config=config,
    )
    failed_email = invite_user_with_retry(user_service, config, payload)
    if failed_email:
        write_failed_invite(supabase_client, payload, "Failed to invite user.")
        return Response(f"Failed to invite user: {failed_email}", status=500)
    return Response("Success", status=200)
