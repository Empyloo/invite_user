import pytest
from src.get_link_type import generate_link_type


def test_generate_link_type_invite():
    payload = {"redirect_to": "/set-password"}
    assert generate_link_type(payload) == "invite"


def test_generate_link_type_magiclink():
    payload = {"redirect_to": "/survey"}
    assert generate_link_type(payload) == "magiclink"


def test_generate_link_type_recover():
    payload = {"redirect_to": "/reset-password"}
    assert generate_link_type(payload) == "recover"


def test_generate_link_type_invalid():
    payload = {"redirect_to": "/invalid"}
    with pytest.raises(ValueError):
        generate_link_type(payload)
