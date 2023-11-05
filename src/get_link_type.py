def generate_link_type(payload: dict) -> str:
    """
    Generate the link type depending on `payload["redirect_to"]`.
    If `payload["redirect_to"]` is a /set-password route, return "recover".
    If `payload["redirect_to"]` is a /survey route, return "magiclink".

    Args:
        payload: dict
    Raises:
        ValueError: If `payload["redirect_to"]` is not a valid route.
    """

    if "/set-password" in payload["redirect_to"]:
        return "invite"
    if "/reset-password" in payload["redirect_to"]:
        return "recover"
    if "/survey" in payload["redirect_to"]:
        return "magiclink"
    raise ValueError("Invalid redirect_to value")
