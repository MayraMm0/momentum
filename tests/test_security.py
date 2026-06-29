from backend.security import hash_password, verify_password

def test_hash_password_returns_different_string_than_input():
    plain = "mysecretpassword"
    hashed = hash_password(plain)
    
    assert hashed != plain
    assert len(hashed) > 0
    
    
def test_verify_password_accepts_correct_and_rejects_wrong():
    plain = "mysecretpassword"
    hashed = hash_password(plain)
    
    assert verify_password(plain, hashed) is True
    assert verify_password("wrongpassword", hashed) is False