import pytest
from fastapi.testclient import TestClient
from pwdlib import PasswordHash
from sqlalchemy import select

from app.auth import TOKEN_TTL_SECONDS
from app.db_models import AccountRow, TokenRow
from app.main import create_app

CREDENTIALS = {"username": "Alice", "password": "a long password"}


def test_registration_login_profile_and_hashed_storage(client):
    registered = client.post("/api/auth/register", json=CREDENTIALS)
    assert registered.status_code == 201
    user = registered.json()
    assert set(user) == {"id", "username"} and user["username"] == "alice"
    with client.app.state.database.sessions() as session:
        account = session.scalar(select(AccountRow).where(AccountRow.username == "alice"))
    assert account.password_hash.startswith("$argon2id$")
    assert PasswordHash.recommended().verify(CREDENTIALS["password"], account.password_hash)
    duplicate = client.post("/api/auth/register", json={**CREDENTIALS, "username": "ALICE"})
    assert duplicate.status_code == 409
    login = client.post("/api/auth/login", json=CREDENTIALS)
    assert login.status_code == 200
    token = login.json()
    assert token["token_type"] == "bearer" and token["expires_in"] == 3600
    with client.app.state.database.sessions() as session:
        digests = session.scalars(select(TokenRow.digest)).all()
        assert len(digests) == 1 and len(digests[0]) == 64
        assert token["access_token"] not in digests
    me = client.get("/api/auth/me", headers={"Authorization": "Bearer " + token["access_token"]})
    assert me.status_code == 200 and me.json() == user
    other = client.post("/api/auth/login", json=CREDENTIALS).json()
    assert other["access_token"] != token["access_token"]


@pytest.mark.parametrize("header", [None, "Bearer unknown", "Basic abc", "Bearer"])
def test_profile_requires_valid_bearer(client, header):
    response = client.get("/api/auth/me", headers={"Authorization": header} if header else {})
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json()["code"] == "unauthorized"


def test_wrong_password_and_unknown_user_have_same_error(client):
    client.post("/api/auth/register", json=CREDENTIALS)
    bad = client.post("/api/auth/login", json={**CREDENTIALS, "password": "incorrect password"})
    unknown = client.post("/api/auth/login", json={**CREDENTIALS, "username": "unknown"})
    assert bad.status_code == unknown.status_code == 401
    assert bad.json() == unknown.json()
    assert CREDENTIALS["password"] not in bad.text


def test_tokens_survive_restart_but_expire(tmp_path):
    now = [1000.0]
    url = f"sqlite:///{tmp_path / 'auth.db'}"
    with TestClient(create_app(database_url=url, clock=lambda: now[0])) as client:
        client.post("/api/auth/register", json=CREDENTIALS)
        token = client.post("/api/auth/login", json=CREDENTIALS).json()["access_token"]
        headers = {"Authorization": "Bearer " + token}
        assert client.get("/api/auth/me", headers=headers).status_code == 200
    with TestClient(create_app(database_url=url, clock=lambda: now[0])) as fresh:
        assert fresh.get("/api/auth/me", headers=headers).status_code == 200
        assert fresh.post("/api/auth/login", json=CREDENTIALS).status_code == 200
        now[0] += TOKEN_TTL_SECONDS
        assert fresh.get("/api/auth/me", headers=headers).status_code == 401
    with TestClient(create_app(database_url=f"sqlite:///{tmp_path / 'other.db'}")) as other:
        assert other.get("/api/auth/me", headers=headers).status_code == 401


def test_passwords_not_trimmed_and_validation_does_not_echo_secrets(client):
    credentials = {"username": "padded", "password": "  password  "}
    assert client.post("/api/auth/register", json=credentials).status_code == 201
    assert client.post("/api/auth/login", json=credentials).status_code == 200
    assert (
        client.post("/api/auth/login", json={**credentials, "password": "password"}).status_code
        == 401
    )
    bad = client.post("/api/auth/register", json={"username": "other", "password": "secret"})
    assert bad.status_code == 422 and "secret" not in bad.text


def test_public_event_routes_ignore_optional_auth(client):
    # Even an invalid optional token must not make public routes require login.
    response = client.post("/api/events/demo", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 201
    assert client.get("/api/events/" + response.json()["id"]).status_code == 200
