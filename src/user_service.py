# Path: user_service.py
import httpx
from typing import Dict, Optional
from tenacity import retry, wait_exponential, stop_after_attempt


class UserService:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {
            "apikey": api_key,
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=30), stop=stop_after_attempt(5)
    )
    def invite_user_by_email(
        self,
        email: str,
        data: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """Invite a user by email.

        Args:
            email: The email address of the user to invite.
            data: Additional data to be sent with the invitation.

        Returns:
            A response object containing the result of the operation.
        """
        payload = {"email": email}
        if data:
            payload["data"] = data

        return httpx.post(
            f"{self.base_url}/auth/v1/invite", headers=self.headers, json=payload
        )

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=30), stop=stop_after_attempt(5)
    )
    def generate_and_send_user_link(
        self,
        email: str,
        link_type: str = "magiclink",
    ) -> httpx.Response:
        """Generate and send a user link.

        Args:
            email: The email address of the user.
            link_type: The type of link to generate (default is "magiclink").

        Returns:
            A response object containing the result of the operation.
        """
        payload = {"email": email}

        return httpx.post(
            f"{self.base_url}/auth/v1/{link_type}",
            headers=self.headers,
            json=payload,
        )

    def get_user(self, user_token: str) -> httpx.Response:
        """Get a user by their token.

        Args:
            user_token: The user's token.

        Returns:
            A response object containing the user's information.
        """
        headers = {**self.headers, "Authorization": f"Bearer {user_token}"}

        return httpx.get(f"{self.base_url}/auth/v1/user", headers=headers)

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=30), stop=stop_after_attempt(5)
    )
    def update_user(
        self,
        user_token: str,
        email: Optional[str] = None,
        password: Optional[str] = None,
        data: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """Update a user's information.

        Args:
            user_token: The user's token.
            email: The new email address (optional).
            password: The new password (optional).
            data: Additional data to update (optional).

        Returns:
            A response object containing the result of the operation.
        """
        headers = {**self.headers, "Authorization": f"Bearer {user_token}"}
        payload = {}
        if email:
            payload["email"] = email
        if password:
            payload["password"] = password
        if data:
            payload["data"] = data

        return httpx.put(f"{self.base_url}/auth/v1/user", headers=headers, json=payload)

        # use admin endpoint to generate a invite link for a user

    def generate_invite_link(
        self,
        email: str,
        data: Optional[Dict[str, str]] = None,
        redirect_to: Optional[str] = None,
        type: str = "invite",
    ) -> httpx.Response:
        """Generate a invite link for a user.

        Args:
            email: The email address of the user to invite.
            data: Additional data to be sent with the invitation.
            redirect_to: URL to redirect the user after accepting the invite.
            type: The type of link to generate (default is "invite").

        Returns:
            A response object containing the result of the operation.
        """
        payload = {"email": email, "type": type}
        if data:
            payload["data"] = data
        if type:
            payload["type"] = type
        if redirect_to:
            payload["redirect_to"] = redirect_to

        return httpx.post(
            f"{self.base_url}/auth/v1/admin/generate_link",
            headers=self.headers,
            json=payload,
        )


if __name__ == "__main__":
    from main import REDIRECT_URL
    from dotenv import load_dotenv
    import os

    load_dotenv()

    SUPABASE_URL = os.getenv("PROD_SUPABASE_URL")
    SUPABASE_KEY = os.getenv("PROD_SUPABASE_SERVICE_ROLE_KEY")

    user_service = UserService(SUPABASE_URL, SUPABASE_KEY)
    email = "sdf@gmail.com"
    payload = {
        "company_name": "Company",
        "company_id": "sdfs-sdf-asd-9a36-asdf",
        "role": "user",
    }
    redirect_to = REDIRECT_URL
    try:
        response = user_service.invite_user_by_email(email, payload, redirect_to)
        print(response.json())
        if response.status_code == 422:
            send_user_link = user_service.generate_and_send_user_link(
                email, "recover", redirect_to
            )
            print(send_user_link.json())

    except Exception as error:
        print("Error")
        print(error)

    try:
        response = user_service.generate_invite_link(email, payload, redirect_to)
        print(response.json())
    except Exception as error:
        print("Error")
        print(error)
