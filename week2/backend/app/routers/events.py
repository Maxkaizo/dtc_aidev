from typing import Annotated

from fastapi import APIRouter, Depends, Request

from ..models import CreateEventRequest, CreateExpenseRequest, CreateGroupRequest, Error, Event
from ..store import EventStore

router = APIRouter(prefix="/api/events", tags=["Events"])


def get_store(request: Request) -> EventStore:
    return request.app.state.store


Store = Annotated[EventStore, Depends(get_store)]
errors = {404: {"model": Error}, 422: {"model": Error}}


@router.post(
    "",
    response_model=Event,
    status_code=201,
    operation_id="createEvent",
    responses={422: {"model": Error}},
    openapi_extra={"security": []},
)
def create_event(data: CreateEventRequest, store: Store):
    return store.create(data)


@router.post(
    "/demo",
    response_model=Event,
    status_code=201,
    operation_id="createDemo",
    openapi_extra={"security": []},
)
def create_demo(store: Store):
    return store.create_demo()


@router.get(
    "/{eventId}",
    response_model=Event,
    operation_id="getEvent",
    responses={404: {"model": Error}},
    openapi_extra={"security": []},
)
def get_event(eventId: str, store: Store):
    return store.get(eventId)


@router.post(
    "/{eventId}/groups",
    response_model=Event,
    status_code=201,
    operation_id="addGroup",
    responses=errors,
    openapi_extra={"security": []},
)
def add_group(eventId: str, data: CreateGroupRequest, store: Store):
    return store.add_group(eventId, data)


@router.post(
    "/{eventId}/expenses",
    response_model=Event,
    status_code=201,
    operation_id="addExpense",
    responses=errors,
    openapi_extra={"security": []},
)
def add_expense(eventId: str, data: CreateExpenseRequest, store: Store):
    return store.add_expense(eventId, data)
