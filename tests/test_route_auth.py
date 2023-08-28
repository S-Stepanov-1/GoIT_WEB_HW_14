import pytest

from unittest.mock import MagicMock

from my_contacts.database.models import User
from my_contacts.services.auth import auth_service


def test_register_user(client, user, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("my_contacts.services.send_email.send_email", mock_send_email)
    response = client.post("api/auth/signup", params=user)

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["user"][1] == user.get("user_email")
    assert data["detail"] == "User successfully created. Check your email for confirmation."


def test_register_user_existing_user(client, user):
    response = client.post("api/auth/signup", params=user)
    assert response.status_code == 409, response.text
    data = response.json()
    assert data["detail"] == "User already exists"


def test_login_user_not_confirmed(client, user):
    response = client.post("api/auth/login", data={"username": user.get("user_email"),
                                                   "password": user.get("password")})

    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Please confirm your account"


def test_login_user_success(client, user, session):
    current_user: User = session.query(User).filter_by(user_email=user.get("user_email")).first()
    current_user.confirmed = True
    session.commit()
    response = client.post("api/auth/login", data={"username": user.get("user_email"),
                                                   "password": user.get("password")})

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["token_type"] == "bearer"


def test_login_user_wrong_password(client, user, session):
    response = client.post("api/auth/login",
                           data={"username": user.get("user_email"),
                                 "password": "<PASSWORD>"})
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Incorrect username or password"


@pytest.mark.asyncio
async def test_refresh_token(client, user, session, monkeypatch):
    user_email = user["user_email"]
    refresh_token = await auth_service.create_refresh_token(data={"sub": user_email})

    new_username = "new_username"
    new_email = "new_email@example.com"
    session.add(User(username=new_username, user_email=new_email, password=user["password"],
                     refresh_token=refresh_token))
    session.commit()

    mock_send_email = MagicMock()
    monkeypatch.setattr("my_contacts.services.send_email.send_email", mock_send_email)

    response = client.get("api/auth/refresh_token", headers={"Authorization": f"Bearer {refresh_token}"})

    assert response.status_code == 200, response.text
    data = response.json()
    assert "new_access_token" in data
    assert "refresh_token" in data


if __name__ == "__main__":
    pytest.main(["-v", "tests/test_route_auth.py"])
