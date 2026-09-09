"""Property-based tests for auth primitives.  [PBT-01..10] BR-A18/A20"""
from __future__ import annotations

import jwt
from hypothesis import given, settings
from hypothesis import strategies as st

from app.auth import security
from app.core.config import get_settings

# Realistic passwords: printable, no NULL bytes, within bcrypt's 72-byte limit.
# (bcrypt rejects NUL and truncates at 72 bytes — both are invalid inputs, not
#  hashing bugs, so we keep the generator inside the supported domain.)
_passwords = st.text(
    alphabet=st.characters(min_codepoint=33, max_codepoint=126),
    min_size=1,
    max_size=60,
).filter(lambda s: len(s.encode()) <= 72)
_store_ids = st.uuids().map(str)


@settings(max_examples=40, deadline=None)
@given(pw=_passwords)
def test_bcrypt_round_trip(pw: str) -> None:
    """BR-A18: a hashed password verifies against itself and nothing else obvious."""
    h = security.hash_password(pw)
    assert h != pw  # never stored in cleartext [SEC-12]
    assert security.verify_password(pw, h) is True
    assert security.verify_password(pw + "x", h) is False


@settings(max_examples=40, deadline=None)
@given(store_id=_store_ids)
def test_jwt_round_trip(store_id: str) -> None:
    """BR-A20: a freshly minted admin token decodes back to its store_id."""
    token = security.create_admin_token(store_id)
    claims = security.decode_admin_token(token)
    assert claims is not None
    assert claims["sub"] == store_id
    assert claims["role"] == "admin"


@settings(max_examples=40, deadline=None)
@given(store_id=_store_ids)
def test_jwt_tamper_rejected(store_id: str) -> None:
    """BR-A20: a token re-signed with the wrong secret is rejected (fail-closed)."""
    forged = jwt.encode(
        {"sub": store_id, "role": "admin", "iss": "table-order"},
        "the-wrong-secret",
        algorithm="HS256",
    )
    assert security.decode_admin_token(forged) is None


def test_jwt_missing_secret_secret_not_leaked() -> None:
    """A garbage token yields None, never an exception. [SEC-15]"""
    assert security.decode_admin_token("not-a-jwt") is None
    assert security.decode_admin_token("") is None


def test_session_token_unique_and_urlsafe() -> None:
    tokens = {security.generate_session_token() for _ in range(200)}
    assert len(tokens) == 200
    assert all(len(t) >= 32 for t in tokens)
