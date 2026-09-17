"""Optional accounts with Argon2 passwords and expiring opaque bearer tokens."""

from collections.abc import Callable
from dataclasses import dataclass
from hashlib import sha256
from secrets import token_urlsafe
from threading import RLock
from time import time
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from pydantic import Field, StringConstraints

from .models import Model
from .store import StoreError

TOKEN_TTL_SECONDS = 3600
Username = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        to_lower=True,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_.-]+$",
    ),
]


class Credentials(Model):
    username: Username
    # Never strip or otherwise normalize passwords.
    password: Annotated[str, Field(min_length=8, max_length=128)]


class User(Model):
    id: str
    username: str


class Token(Model):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int = TOKEN_TTL_SECONDS


@dataclass(frozen=True)
class Account:
    id: str
    username: str
    password_hash: str


class AuthStore:
    def __init__(self, clock: Callable[[], float] = time):
        self._lock = RLock()
        self._clock = clock
        self._hasher = PasswordHash.recommended()
        self._dummy_hash = self._hasher.hash(token_urlsafe(32))
        self._accounts: dict[str, Account] = {}
        # Only SHA-256 token digests are stored, never raw bearer tokens.
        self._tokens: dict[str, tuple[str, float]] = {}

    def register(self, data: Credentials) -> User:
        password_hash = self._hasher.hash(data.password)
        with self._lock:
            if data.username in self._accounts:
                raise StoreError(409, "username_taken", "Ese nombre de usuario ya está registrado.")
            account = Account(str(uuid4()), data.username, password_hash)
            self._accounts[account.username] = account
            return User(id=account.id, username=account.username)

    def login(self, data: Credentials) -> Token:
        with self._lock:
            account = self._accounts.get(data.username)
        valid = self._hasher.verify(
            data.password, account.password_hash if account else self._dummy_hash
        )
        if not valid or account is None:
            raise unauthorized()
        token = token_urlsafe(32)
        now = self._clock()
        with self._lock:
            self._tokens = {key: value for key, value in self._tokens.items() if value[1] > now}
            self._tokens[sha256(token.encode()).hexdigest()] = (
                account.username,
                now + TOKEN_TTL_SECONDS,
            )
        return Token(access_token=token)

    def authenticate(self, token: str) -> User:
        digest = sha256(token.encode()).hexdigest()
        with self._lock:
            session = self._tokens.get(digest)
            if session is None or session[1] <= self._clock():
                self._tokens.pop(digest, None)
                raise unauthorized()
            account = self._accounts[session[0]]
            return User(id=account.id, username=account.username)


def unauthorized() -> StoreError:
    return StoreError(401, "unauthorized", "Credenciales o token inválidos o vencidos.")


def get_auth(request: Request) -> AuthStore:
    return request.app.state.auth


bearer = HTTPBearer(auto_error=False, scheme_name="BearerAuth")


def current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    auth: Annotated[AuthStore, Depends(get_auth)],
) -> User:
    if credentials is None:
        raise unauthorized()
    return auth.authenticate(credentials.credentials)
