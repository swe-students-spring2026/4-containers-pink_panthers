from werkzeug.security import generate_password_hash
from unittest.mock import patch


def test_signup_page_loads(client):
    """Test that the signup page loads successfully."""
    response = client.get("/signup")
    assert response.status_code == 200
    assert b"Sign Up" in response.data


def test_signup_rejects_mismatched_passwords(client):
    """Test that signup fails when password and confirm_password do not match."""
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


def test_signup_success_redirects_to_login(client):
    """Test that a successful signup redirects to the login page."""
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


def test_signup_rejects_existing_user(client):
    """Test that signup fails when the username already exists."""
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


def test_login_rejects_wrong_password(client):
    """Test that login fails when the password is incorrect."""
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


def test_login_success_sets_session(client):
    """Test that a successful login sets the session and redirects."""
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


def test_logout_clears_session(client):
    """Test that logging out clears the session and redirects to login."""
    with client.session_transaction() as sess:
        sess["user_id"] = "abc123"
        sess["username"] = "sara123"

    response = client.get("/logout", follow_redirects=False)

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

    with client.session_transaction() as sess:
        assert "user_id" not in sess
        assert "username" not in sess


def test_index_redirects_to_login_when_logged_out(client):
    """Test that accessing the index page when not logged in redirects to the login page."""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_analyze_requires_login(client):
    """Test that accessing the analyze page when not logged in redirects to the login page."""
    response = client.get("/analyze", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_api_outfit_requires_login(client):
    """Test that accessing the API outfit endpoint when not logged in redirects to the login page."""
    response = client.post(
        "/api/outfit",
        json={"top": "#ffffff", "bottom": "#000000", "photo": "dummy"},
    )
    assert response.status_code == 401
    data = response.get_json()
    assert data["error"] == "authentication_required"


@patch("app.get_outfits_by_user", return_value=[])
@patch("app.get_all_outfits", return_value=[])
def test_stats_requires_login(mock_all, mock_user, client):
    """Test that accessing the stats page when not logged in redirects to the login page."""
    response = client.get("/stats", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


@patch("app.get_outfits_by_user", return_value=[])
def test_outfits_requires_login(mock_user, client):
    """Test that outfits requires login."""
    response = client.get("/outfits", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_index_redirects_to_analyze_when_logged_in(client):
    """Test that accessing the index page when logged in redirects to the analyze page."""
    with client.session_transaction() as sess:
        sess["user_id"] = "abc123"
        sess["username"] = "sara123"

    response = client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert "/analyze" in response.headers["Location"]


def test_login_page_loads(client):
    """Test that the login page loads successfully."""
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Log In" in response.data


def test_signup_rejects_short_password(client):
    """Test that the signup page rejects short passwords."""
    response = client.post(
        "/signup",
        data={
            "username": "sara123",
            "password": "123",
            "confirm_password": "123",
        },
    )
    assert response.status_code == 200
    assert b"Password must be at least 8 characters long." in response.data


def test_analyze_loads_when_logged_in(client):
    """Test that the analyze page loads when the user is logged in."""
    with client.session_transaction() as sess:
        sess["user_id"] = "abc123"
        sess["username"] = "sara123"

    response = client.get("/analyze")
    assert response.status_code == 200


@patch("app.get_outfits_by_user", return_value=[])
@patch("app.get_all_outfits", return_value=[])
def test_stats_loads_when_logged_in(mock_all, mock_user, client):
    """Test that the stats page loads when the user is logged in."""
    with client.session_transaction() as sess:
        sess["user_id"] = "abc123"
        sess["username"] = "sara123"

    response = client.get("/stats")
    assert response.status_code == 200


@patch("app.get_outfits_by_user", return_value=[])
def test_outfits_loads_when_logged_in(mock_user, client):
    """Test that outfits page loads when logged in."""
    with client.session_transaction() as sess:
        sess["user_id"] = "abc123"
        sess["username"] = "sara123"
    response = client.get("/outfits")
    assert response.status_code == 200
