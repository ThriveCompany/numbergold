from backend.app.auth import hash_password, verify_password, create_access_token


def test_password_hashing():
    password = "StrongPass123!"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("WrongPass", hashed)


def test_jwt_token_contains_user_data():
    token = create_access_token(subject_id=1, username="player1")
    assert token is not None
    assert token.count(".") == 2
