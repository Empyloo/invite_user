# invite_user

Invite user cloud function code base.

## Overview

This cloud function is designed to invite a user to join a specific group or organization. It sends an email to the user with a link to accept the invitation.

## Requirements

- Python 3.10 or higher
- The following Python packages:
  - fastapi
  - tenacity
  - pydantic
  - supabase
  - functions-framework
  - python-dotenv
  - google-crc32c
  - google-cloud-secret-manager

## Installation

To set-up the `venv`:
- `pyenv local 3.10.8`
- `python -m venv venv`
- `source venv/bin/activate`

To install the necessary packages, run the following command in the root directory of the project:

```bash
pip install -r requirements.txt
```

## Make Targets

- `make test` - runs the pytest module to run unit tests
- `make lint` - checks the code for style and formatting issues using flake8
- `make format` - runs isort to sort imports and black to format the code
- `make run` - runs the functions-framework with the main target in debug mode
- `make install` - installs the required packages specified in the requirements.txt file
- `make install-dev` - installs the required packages for development, specified in the requirements-dev.txt file
- `make install-all` - installs all required packages, including those for development

To run a make target, use the `make` command followed by the target name. For example, to run the `test` target, you can use the following command:

```bash
make test
```

## Posting a Request to the Cloud Function
```
curl -m 70 -X POST https://invite-user-function-wojn2zefia-nw.a.run.app \
-H "Authorization: bearer $(gcloud auth print-identity-token)" \
-H "Content-Type: application/json" \
-d '{
  "email": "buser@example.com",
  "company_name": "Empylo",
  "company_id": "asdfaff-6316-472d-9a36-asdfaf",
  "role": "super_admin"
}'
```


# Running the Cloud Function and Posting a Request

Follow the steps below to run the cloud function locally and post a request to it.

## Prerequisites

- Make sure you have followed the installation steps above.


## Steps

1. **Set up your environment variables**: Create a `.env` file in the root directory of your project and add the following variables:

```bash
SUPABASE_URL=your_supabase_url
SERVICE_ROLE_KEY=your_service_role_key
```

Replace `your_supabase_url` and `your_service_role_key` with your actual Supabase URL and service role key.

2. **Start the Functions Framework**: Run the following command in your terminal to start the Functions Framework:

```bash
functions-framework --target=main
```

This will start the Functions Framework on localhost on port 8080.

3. **Post a request to the function**: You can use `curl` or any API client like Postman to send a POST request to the function. Here's an example using `curl`:

```bash
curl -X POST http://localhost:8080 -H "Content-Type: application/json" -d '{"email":"user@example.com","company_id":"your_company_id","company_name":"your_company_name","role":"your_role"}'
```

Replace `user@example.com`, `your_company_id`, `your_company_name`, and `your_role` with the actual email, company ID, company name, and role of the user you want to invite.

You should see a response from the function in your terminal.

## Troubleshooting

If you encounter any issues, check the logs in your terminal for any error messages. Make sure your Supabase URL and service role key are correct and that the user you're trying to invite doesn't already exist.