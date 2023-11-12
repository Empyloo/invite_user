import os
import logging
import psycopg2


def is_password_set(db_url: str, email: str) -> str:
    """
    Checks if a user's password is set in the database.

    Parameters
    ----------
    db_url : str
        The database connection string.
    email : str
        The user's email.

    Returns
    -------
    str
        "user not found" if the user doesn't exist,
        "password not set" if the user exists but password is not set,
        "password set" if the user exists and password is set.
    """
    try:
        with psycopg2.connect(db_url) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT encrypted_password FROM auth.users WHERE email = %s",
                    (email,),
                )
                result = cursor.fetchone()
                if result is None:
                    raise Exception("User not found")
                elif result[0] is None:
                    return "password not set"
                else:
                    return "password set"
    except Exception as e:
        logging.error(f"Error checking if password is set for user {email}: {e}")
        raise e


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    db_url = os.getenv("SUPABASE_POSTGRES_CONNECTION_STRING")
    email = "june@may.com" # os.getenv("FIRST_EMAIL")
    is_set = is_password_set(db_url=db_url, email=email)
    print(f"Password set for user {email}: {is_set}")
