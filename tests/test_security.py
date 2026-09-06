from domain_services.security import decrypt, encrypt, hash_password, verify_password


def test_hash_verify_roundtrip() -> None:
    hashed = hash_password("correct horse battery staple")
    assert verify_password("correct horse battery staple", hashed)
    assert not verify_password("wrong password", hashed)


def test_hash_is_not_plaintext() -> None:
    assert "hunter2" not in hash_password("hunter2")


def test_verify_handles_malformed_hash() -> None:
    assert verify_password("x", "not-a-bcrypt-hash") is False


def test_encrypt_decrypt_roundtrip() -> None:
    token = encrypt("Jane Doe, 555-0100")
    assert token != "Jane Doe, 555-0100"
    assert decrypt(token) == "Jane Doe, 555-0100"


def test_ciphertext_is_non_deterministic() -> None:
    assert encrypt("same") != encrypt("same")

