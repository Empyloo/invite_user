from main import REDIRECT_URL, create_supabase_client

supabase_client = create_supabase_client()
email = "chitiyobrian@gmail.com"
payload = {
    "company_name": "Empylo",
    "company_id": "ad5d3ab9-6316-472d-9a36-6e9bf9417580",
    "role": "user",
}

supabase_client.auth.api.invite_user_by_email(
    email=email, data=payload, redirect_to=REDIRECT_URL
)
