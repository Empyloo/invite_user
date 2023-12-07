from typing import Any, Dict, Optional
from supacrud import Supabase, ResponseType
from tenacity import retry, wait_exponential, stop_after_attempt


class UserService:
    def __init__(self, client: Supabase, config: dict):
        self.config = config
        self.client = client


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

        return self.client.create("auth/v1/invite", data=payload)


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
            url=f"auth/v1/{link_type}",
            data=payload,
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
        add_to_headers = {"Authorization": f"Bearer {user_token}"}
        self.client.update_headers(add_to_headers)
        payload = {}
        if email:
            payload["email"] = email
        if password:
            payload["password"] = password
        if data:
            payload["data"] = data

        return self.client.update("auth/v1/user", data=payload)

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
        headers = {
            "apikey": self.config["supabase_service_key"],
            "Authorization": f"Bearer {self.config['supabase_service_key']}",
        }
        self.client.update_headers(headers)
        return self.client.create(
            url="auth/v1/admin/generate_link",
            data=payload,
        )
