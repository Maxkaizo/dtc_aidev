from typing import Annotated

from fastapi import APIRouter, Depends

from ..auth import AuthStore, Credentials, Token, User, current_user, get_auth
from ..models import Error

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
Auth = Annotated[AuthStore, Depends(get_auth)]


@router.post(
    "/register",
    status_code=201,
    response_model=User,
    operation_id="register",
    responses={409: {"model": Error}, 422: {"model": Error}},
    openapi_extra={"security": []},
)
def register(data: Credentials, auth: Auth):
    return auth.register(data)


@router.post(
    "/login",
    response_model=Token,
    operation_id="login",
    responses={401: {"model": Error}, 422: {"model": Error}},
    openapi_extra={"security": []},
)
def login(data: Credentials, auth: Auth):
    return auth.login(data)


@router.get(
    "/me", response_model=User, operation_id="getCurrentUser", responses={401: {"model": Error}}
)
def me(user: Annotated[User, Depends(current_user)]):
    return user
