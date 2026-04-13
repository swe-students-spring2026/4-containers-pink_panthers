from werkzeug.security import generate_password_hash
from unittest.mock import patch


# signup page can be opened
def test_signup_page_loads(client):
    response = client.get("/signup")
    assert response.status_code == 200
    assert b"Sign Up" in response.data


# signup password not same
def test_signup_rejects_mismatched_passwords(client):
    response = client.post(
        "/signup",
        data={
            "username": "sara",
            "password": "12345678",
            "confirm_password": "abcdefgh",
        },
    )
    assert response.status_code == 200
    assert b"Passwords do not match." in response.data


# Test signup success: new user -> redirect to login
def test_signup_success_redirects_to_login(client):
    with patch("app.find_user_by_username", return_value=None), patch(
        "app.create_user"
    ) as mock_create_user:
        response = client.post(
            "/signup",
            data={
                "username": "sara123",
                "password": "12345678",
                "confirm_password": "12345678",
            },
            follow_redirects=False,
        )

        assert response.status_code == 302
        assert "/login" in response.headers["Location"]
        mock_create_user.assert_called_once()


# Test signup with existing username -> show error message
def test_signup_rejects_existing_user(client):
    with patch("app.find_user_by_username", return_value={"username": "sara"}):
        response = client.post(
            "/signup",
            data={
                "username": "sara",
                "password": "12345678",
                "confirm_password": "12345678",
            },
        )

        assert response.status_code == 200
        assert b"Username already exists" in response.data


# Wrong password on login
def test_login_rejects_wrong_password(client):
    fake_user = {
        "_id": "abc123",
        "username": "sara123",
        "password_hash": generate_password_hash("correct-password"),
    }

    with patch("app.find_user_by_username", return_value=fake_user):
        response = client.post(
            "/login",
            data={
                "username": "sara123",
                "password": "wrong-password",
            },
        )

        assert response.status_code == 200
        assert b"Invalid username or password." in response.data


# if login successfully, session should be set
def test_login_success_sets_session(client):
    fake_user = {
        "_id": "507f1f77bcf86cd799439011",
        "username": "sara123",
        "password_hash": generate_password_hash("12345678"),
    }

    with patch("app.find_user_by_username", return_value=fake_user), patch(
        "app.update_last_login"
    ) as mock_update_last_login:
        response = client.post(
            "/login",
            data={
                "username": "sara123",
                "password": "12345678",
            },
            follow_redirects=False,
        )

        assert response.status_code == 302
        assert "/analyze" in response.headers["Location"]

        with client.session_transaction() as sess:
            assert sess["user_id"] == "507f1f77bcf86cd799439011"
            assert sess["username"] == "sara123"

        mock_update_last_login.assert_called_once()


# if logout, session should be cleared
def test_logout_clears_session(client):
    with client.session_transaction() as sess:
        sess["user_id"] = "abc123"
        sess["username"] = "sara123"

    response = client.get("/logout", follow_redirects=False)

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

    with client.session_transaction() as sess:
        assert "user_id" not in sess
        assert "username" not in sess
