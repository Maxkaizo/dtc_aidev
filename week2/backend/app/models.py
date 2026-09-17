"""Request and response models matching the frontend's camelCase wire format."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Category = Literal["food", "drinks", "games", "general"]
Currency = Literal["MXN", "USD", "EUR"]
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]
EventName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Description = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
Id = Annotated[str, StringConstraints(min_length=1)]
Cents = Annotated[int, Field(strict=True, ge=1, le=10_000_000_000)]


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateEventRequest(Model):
    name: EventName
    currency: Currency


class CreateAttendeeRequest(Model):
    name: Name
    categories: list[Category]


class CreateGroupRequest(Model):
    name: Name
    representative: Name
    attendees: Annotated[list[CreateAttendeeRequest], Field(min_length=1)]


class CreateExpenseRequest(Model):
    description: Description
    amount: Cents
    category: Category
    groupId: Id


class Attendee(CreateAttendeeRequest):
    id: Id


class Group(Model):
    id: Id
    name: Name
    representative: Name
    attendees: list[Attendee]


class Expense(CreateExpenseRequest):
    id: Id


class Event(CreateEventRequest):
    id: Id
    groups: list[Group]
    expenses: list[Expense]


class Error(Model):
    code: str
    message: str
