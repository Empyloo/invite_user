import logging
from multiprocessing.connection import wait
import subprocess
import time
import socket
import os

logger = logging.getLogger(__name__)


def reset_env_file(credentials: dict) -> bool:
    """Updates the .env file with the provided credentials.
    Returns True if the update was successful, False otherwise.
    """
    env_vars = "\n".join([f"{k.upper()}={v}" for k, v in credentials.items()])
    logger.info("Updating .env file with: %s", env_vars)
    with open(".env", "w") as env_file:
        env_file.write(env_vars)
    for key, value in credentials.items():
        if os.environ.get(key.upper()) != value:
            return False
    return True


def supabase_init() -> bool:
    """Starts Supabase init"""
    try:
        result = subprocess.run(
            ["supabase", "init", "--workdir", "supabase"],
            capture_output=True,
            text=True,
            check=True,
        )
        if result.stdout:
            logger.info("Supabase init: %s", result.stdout)
            return True
        logger.error("Error starting Supabase init: %s", result.stderr)
        return False
    except subprocess.CalledProcessError as error:
        if "Supabase is already running" in error.stderr:
            logger.warning("Supabase is already running")
            return True
        logger.error("Error starting Supabase init: %s", error)
        return False


def start_supabase() -> bool:
    try:
        result = subprocess.run(
            ["supabase", "start", "--workdir", "supabase"],
            capture_output=True,
            text=True,
            check=True,
        )
        if result.stdout:
            logger.info("Supabase started: %s", result.stdout)
            return True
        logger.error("Error starting Supabase: %s", result.stderr)
        return False
    except subprocess.CalledProcessError as error:
        if "Supabase is already running" in error.stderr:
            logger.warning("Supabase is already running")
            return True
        elif "Error" in error.stderr and "config" in error.stderr:
            logger.warning("Supabase not initialized, initializing...")
            supabase_init()
            stop_supabase()
            return True
        logger.error("Error starting Supabase: %s", error)
        return False
    except Exception as error:
        logger.error("Error starting Supabase: %s", error)
        return False


def stop_supabase() -> bool:
    try:
        result = subprocess.run(
            ["supabase", "stop", "--workdir", "supabase"],
            capture_output=True,
            text=True,
            check=True,
        )
        if "Stopped" in result.stdout:
            logger.info("Supabase stopped: %s", result.stdout)
            return True
        logger.error("Error stopping Supabase: %s", result.stderr)
        return False
    except subprocess.CalledProcessError as error:
        if "Error" in error.stderr and "config" in error.stderr:
            logger.warning("Supabase not initialized, initializing...")
            supabase_init()
            stop_supabase()
            return True
        logger.error("Error args stopping Supabase: %s", error.args)
    except Exception as error:
        logger.error("Error stopping Supabase: %s", error)
        return False


def get_supabase_status() -> str | bool:
    """Returns Supabase status or False if error"""
    try:
        result = subprocess.run(
            ["supabase", "status", "--workdir", "supabase"],
            capture_output=True,
            text=True,
            check=True,
        )
        if "DB URL" in result.stdout:
            logger.info("Supabase status: %s", result.stdout)
            return result.stdout
        logger.error("Error getting Supabase status: %s", result.stderr)
        return False
    except Exception as error:
        logger.error("Error getting Supabase status: %s", error)
        return False


def get_db_credentials() -> dict:
    """Returns DB credentials or an empty dictionary if error"""
    try:
        result = subprocess.run(
            ["supabase", "status", "--workdir", "supabase"],
            capture_output=True,
            text=True,
            check=True,
        )
        if result.stdout:
            credentials = {}
            for line in result.stdout.split("\n"):
                if "API URL" in line:
                    host = socket.gethostbyname(socket.gethostname())
                    credentials["supabase_url"] = line.split(": ")[1].replace(
                        "localhost", host
                    )
                elif "DB URL" in line:
                    credentials["db_url"] = line.split(": ")[1]
                elif "anon key" in line:
                    credentials["anon_key"] = line.split(": ")[1]
                elif "service_role key" in line:
                    credentials["service_role_key"] = line.split(": ")[1]
            return credentials
        logger.error("Error getting DB credentials: %s", result.stderr)
        return {}
    except Exception as error:
        logger.error("Error getting DB credentials: %s", error)
        return {}


def get_supabase_credentials() -> str:
    """This version will check if Supabase is already running, and if it is, it
    will stop it. It will then start Supabase and wait until it is running or
    an error occurs. If there is an error, it will raise an exception.
    Once Supabase is running, it will retrieve the DB URL and return it.
    """
    if not os.path.isdir("supabase"):
        logger.error("Supabase directory does not exist, creating...")
        os.mkdir("supabase")
        supabase_init()
    status = get_supabase_status()
    success = False
    if status and "DB URL" in status:
        stop_supabase()
        success = False
    start_time = time.time()
    while not success:
        supabase_start = start_supabase()
        if supabase_start:
            success = True
            break
        elif time.time() - start_time > 60:
            logger.error("Error starting Supabase: Timed out")
            raise Exception("Error starting Supabase: Timed out")
        else:
            logger.error("Error starting Supabase.")
            raise Exception("Error starting Supabase.")
    success = False
    start_time = time.time()
    while not success:
        status = get_supabase_status()
        if not status:
            raise Exception(status)
        elif "DB URL" in status:
            success = True
            break
        if time.time() - start_time > 60:
            logger.error("Error starting Supabase: Timed out")
            raise Exception("Error starting Supabase: Timed out")
        time.sleep(1)
    credentials = get_db_credentials()
    if not credentials:
        logger.error("Error getting DB credentials.")
        raise Exception("Error getting DB credentials.")
    reset_env_file(credentials=credentials)
    logger.info("DB credentials: %s", credentials)
    return credentials


if __name__ == "__main__":
    print(get_supabase_credentials())
