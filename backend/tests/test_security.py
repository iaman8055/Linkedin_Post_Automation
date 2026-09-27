from uuid import uuid4

import pytest

from app.core.config import Settings
from app.core.security import (
    AccessTokenError,
    create_access_token,
    decode_access_token,
    hash_opaque_token,
    hash_password,
    verify_password,
)


def test_password_hashing_and_verification() -> None:
    encoded = hash_password("a-strong-password")

    assert encoded != "a-strong-password"
    assert encoded.startswith("$argon2")
    assert verify_password("a-strong-password", encoded)
    assert not verify_password("wrong-password", encoded)


def test_access_token_round_trip() -> None:
    settings = Settings(jwt_secret="test-secret-with-enough-entropy-123")
    user_id = uuid4()

    token, expires_in = create_access_token(user_id, settings)

    assert decode_access_token(token, settings) == user_id
    assert expires_in == 900


def test_access_token_rejects_wrong_secret() -> None:
    issuer_settings = Settings(jwt_secret="issuer-secret-that-is-at-least-32-bytes")
    verifier_settings = Settings(jwt_secret="different-secret-that-is-at-least-32")
    token, _ = create_access_token(uuid4(), issuer_settings)

    with pytest.raises(AccessTokenError):
        decode_access_token(token, verifier_settings)


def test_opaque_token_hash_is_keyed() -> None:
    first = Settings(jwt_secret="first-secret")
    second = Settings(jwt_secret="second-secret")

    assert hash_opaque_token("raw-token", first) != hash_opaque_token("raw-token", second)
