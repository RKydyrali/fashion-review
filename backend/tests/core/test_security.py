from app.domain.roles import UserRole


def test_password_hashing_uses_non_plaintext_and_verifies() -> None:
    from app.core.security import get_password_hash, verify_password

    hashed_password = get_password_hash("clientpass123")

    assert hashed_password != "clientpass123"
    assert verify_password("clientpass123", hashed_password) is True
    assert verify_password("wrong-password", hashed_password) is False


def test_access_token_round_trip_preserves_subject_and_role() -> None:
    from app.core.security import create_access_token, decode_access_token

    token = create_access_token(subject="42", role=UserRole.PRODUCTION)
    payload = decode_access_token(token)

    assert payload.sub == "42"
    assert payload.role == UserRole.PRODUCTION
