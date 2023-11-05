from typing import Any, Dict, Optional
from supacrud import Supabase, SupabaseError, ResponseType
from tenacity import retry, wait_exponential, stop_after_attempt


class UserService:
    def __init__(self, client: Supabase, config: dict):
        self.base_url = config["supabase_url"]
        self.api_key = config["supabase_key"]
        self.headers = {
            "apikey": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        self.config = config
        self.client = client

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=30), stop=stop_after_attempt(5)
    )
    def invite_user_by_email(
        self,
        email: str,
        data: Optional[Dict[str, str]] = None,
    ) -> ResponseType:
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

        return self.client.create(
            f"{self.base_url}/auth/v1/invite", headers=self.headers, json=payload
        )

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=30), stop=stop_after_attempt(3)
    )
    def generate_and_send_user_link(
        self,
        email: str,
        link_type: str = "magiclink",
    ) -> ResponseType:
        """Generate and send a user link.

        Args:
            email: The email address of the user.
            link_type: The type of link to generate (default is "magiclink").

        Returns:
            A response object containing the result of the operation.
        """
        payload = {"email": email}

        return self.client.create(
            f"{self.base_url}/auth/v1/{link_type}",
            headers=self.headers,
            json=payload,
        )

    def get_user(self, user_token: str) -> ResponseType:
        """Get a user by their token.

        Args:
            user_token: The user's token.

        Returns:
            A response object containing the user's information.
        """
        headers = {**self.headers, "Authorization": f"Bearer {user_token}"}

        return self.client.read(f"{self.base_url}/auth/v1/user", headers=headers)

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=30), stop=stop_after_attempt(5)
    )
    def update_user(
        self,
        user_token: str,
        email: Optional[str] = None,
        password: Optional[str] = None,
        data: Optional[Dict[str, str]] = None,
    ) -> ResponseType:
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

        return self.client.update(
            f"{self.base_url}/auth/v1/user", headers=headers, json=payload
        )

    def generate_invite_link(
        self,
        email: str,
        data: Optional[Dict[str, str]] = None,
        redirect_to: Optional[str] = None,
        type: str = "invite",
    ) -> ResponseType:
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

        return self.client.create(
            f"{self.base_url}/auth/v1/admin/generate_link",
            headers=self.headers,
            json=payload,
        )
