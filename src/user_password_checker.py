import os
import logging
import psycopg2

def is_password_set(db_url: str, email: str) -> bool:
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
    bool
        True if the user's password is set, False otherwise.
    """
    try:
        with psycopg2.connect(db_url) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT encrypted_password FROM auth.users WHERE email = %s", (email,))
                result = cursor.fetchone()
                is_set = result is not None and result[0] is not None
                logging.info(f"Password set for user {email}: {is_set}")
                return is_set
    except Exception as e:
        logging.error(f"Error checking if password is set for user {email}: {e}")
        raise e

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    db_url = os.getenv("SUPABASE_POSTGRES_CONNECTION_STRING")
    email = os.getenv("FIRST_EMAIL")
    is_set = is_password_set(db_url=db_url, email=email)
    print(f"Password set for user {email}: {is_set}")
