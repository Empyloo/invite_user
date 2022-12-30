import os
import time
import socket
import threading
import signal
import subprocess
import requests
import logging
from set_db_up import (
    spin_db_up,
    get_supabase_client,
)
from get_supabase_credentials import get_supabase_credentials, stop_supabase

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def run_functions_framework():
    """Run the functions framework command."""
    try:
        subprocess.run(
            "functions-framework --target=main --port=8080",
            shell=True,
            check=True,
        )
    except subprocess.CalledProcessError as error:
        logger.info("%s stopped.", error)
        return False
    return True


def close_functions_framework():
    output = subprocess.run(["ps", "aux"], stdout=subprocess.PIPE).stdout.decode()
    for line in output.splitlines():
        if "functions-framework" in line:
            process_id = line.split()[1]
            os.kill(int(process_id), signal.SIGKILL)


def make_api_request(payload: dict) -> requests.Response:
    """Make a request to the functions framework."""
    try:
        host = socket.gethostbyname(socket.gethostname())
        url = "http://localhost:8080".replace("localhost", host)
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            url=url,
            headers=headers,
            json=payload,
        )
        logger.info("Made request to functions framework: %s", response.text)
        return response
    except requests.exceptions.RequestException as error:
        logger.error("Error making request: %s", error)
        return False


def make_invite(payload: dict) -> bool:
    """Make an invite."""
    try:
        result = make_api_request(payload=payload)
        logger.info("Result: %s", result)
    except Exception as error:
        logger.error("Error making invite: %s", error)
        return False
    return True


def check_user_invited(db_credentials: dict, email: str) -> bool:
    """Check if user invite worked."""
    try:
        supabase_client = get_supabase_client(db_credentials=db_credentials)
        response = (
            supabase_client.from_("users").select("*").eq("email", email).execute()
        )
        logger.info("Response: %s", response)
        if response.data[0]["email"] == email:
            logger.info("User was added to the users table")
            return True
        else:
            logger.error("User was not added to the users table")
            return False
    except Exception as error:
        logger.error("Error testing user invite: %s", error)
        return False


def test_main():
    functions_framework_thread = threading.Thread(target=run_functions_framework)
    close_functions_framework_thread = threading.Thread(
        target=close_functions_framework
    )
    functions_framework_thread.start()
    logger.error("Error running functions framework")
    logger.info("Starting user invite integration test...")
    db_credentials = spin_db_up()
    payload = {
        "email": "test@empylo.com",
        "company_name": "Empylo",
        "company_id": db_credentials["company_id"],
        "role": "member",
    }
    invite_user = make_invite(payload=payload)
    if not invite_user:
        logger.error("Error making invite")
        return False
    user_invited = check_user_invited(
        db_credentials=db_credentials, email=payload["email"]
    )
    if not user_invited:
        logger.error("Seems like the user was not invited. Not working as expeceted.")
        return False
    logger.info("User invite integration test passed!")
    close_functions_framework_thread.start()
    stop_supabase()
    return True


if __name__ == "__main__":
    test_main()
