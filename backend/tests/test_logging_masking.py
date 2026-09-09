"""Sensitive-data masking in structured logs.  [SEC-03][BR-C18]"""
from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from app.core.logging import mask_sensitive


def test_masks_known_sensitive_keys():
    masked = mask_sensitive(
        {
            "username": "admin",
            "password": "supersecret",
            "session_token": "abc.def",
            "admin_password_hash": "$2b$12$...",
            "nested": {"jwt": "x.y.z", "amount": 100},
        }
    )
    assert masked["username"] == "admin"
    assert masked["password"] == "***"
    assert masked["session_token"] == "***"
    assert masked["admin_password_hash"] == "***"
    assert masked["nested"]["jwt"] == "***"
    assert masked["nested"]["amount"] == 100


@given(secret=st.text(min_size=1))
def test_password_value_never_survives(secret):
    masked = mask_sensitive({"password": secret, "token": secret})
    assert masked["password"] == "***"
    assert masked["token"] == "***"


def test_masks_inside_lists():
    masked = mask_sensitive([{"password": "p1"}, {"token": "t1"}])
    assert masked[0]["password"] == "***"
    assert masked[1]["token"] == "***"
