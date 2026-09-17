"""Optional accounts with Argon2 passwords and expiring opaque bearer tokens."""

from collections.abc import Callable
from hashlib import sha256
from secrets import token_urlsafe
from time import time
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from pydantic import Field, StringConstraints
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from .database import Database
from .db_models import AccountRow, TokenRow
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


class AuthStore:
    def __init__(self, database: Database, clock: Callable[[], float] = time):
        self.database = database
        self._clock = clock
        self._hasher = PasswordHash.recommended()
        self._dummy_hash = self._hasher.hash(token_urlsafe(32))

    def register(self, data: Credentials) -> User:
        account = AccountRow(
            id=str(uuid4()), username=data.username, password_hash=self._hasher.hash(data.password)
        )
        try:
            with self.database.sessions.begin() as session:
                session.add(account)
        except IntegrityError:
            with self.database.sessions() as session:
                if (
                    session.scalar(select(AccountRow).where(AccountRow.username == data.username))
                    is None
                ):
                    raise
            raise StoreError(
                409, "username_taken", "Ese nombre de usuario ya está registrado."
            ) from None
        return User(id=account.id, username=account.username)

    def login(self, data: Credentials) -> Token:
        with self.database.sessions() as session:
            account = session.scalar(select(AccountRow).where(AccountRow.username == data.username))
            valid = self._hasher.verify(
                data.password, account.password_hash if account else self._dummy_hash
            )
            if not valid or account is None:
                raise unauthorized()
            account_id = account.id
        token = token_urlsafe(32)
        now = self._clock()
        with self.database.sessions.begin() as session:
            session.execute(delete(TokenRow).where(TokenRow.expires_at <= now))
            session.add(
                TokenRow(
                    digest=sha256(token.encode()).hexdigest(),
                    account_id=account_id,
                    expires_at=now + TOKEN_TTL_SECONDS,
                )
            )
        return Token(access_token=token)

    def authenticate(self, token: str) -> User:
        digest = sha256(token.encode()).hexdigest()
        with self.database.sessions() as session:
            row = session.get(TokenRow, digest)
            if row is None or row.expires_at <= self._clock():
                raise unauthorized()
            account = session.get(AccountRow, row.account_id)
            if account is None:
                raise unauthorized()
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
