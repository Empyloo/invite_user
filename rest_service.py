# Path: rest_service.py
import httpx
from typing import Dict, Optional
from tenacity import retry, wait_exponential, stop_after_attempt


class RestService:
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
    def create(
        self,
        table: str,
        data: Dict[str, str]
    ) -> httpx.Response:
        """Create a new record in the specified table.

        Args:
            table: The name of the table.
            data: A dictionary containing the data to be inserted.

        Returns:
            A response object containing the result of the operation.
        """
        return httpx.post(
            f"{self.base_url}/rest/v1/{table}",
            headers=self.headers,
            json=data,
        )

if __name__ == "__main__":
    from dotenv import load_dotenv
    import os

    load_dotenv()

    SUPABASE_URL = os.getenv("PROD_SUPABASE_URL")
    SUPABASE_KEY = os.getenv("PROD_SUPABASE_SERVICE_ROLE_KEY")

    email = "test@email.com"
    payload = {"email": email, "data": {"error": "Test User"}}
    try:
        rest_service = RestService(base_url=SUPABASE_URL, api_key=SUPABASE_KEY)
        response = rest_service.create(table="users", data=payload)
        print(response.json())
    except Exception as e:
        print(e)