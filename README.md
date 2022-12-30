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