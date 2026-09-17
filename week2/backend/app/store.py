"""Process-local storage with atomic writes and detached read snapshots."""

from threading import RLock
from uuid import uuid4

from .models import (
    Attendee,
    CreateEventRequest,
    CreateExpenseRequest,
    CreateGroupRequest,
    Event,
    Expense,
    Group,
)

MAX_SAFE_INTEGER = 9_007_199_254_740_991
SEED_EVENT_ID = "demo"


class StoreError(Exception):
    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message


def demo_event(event_id: str) -> Event:
    return Event(
        id=event_id,
        name="Domingo entre amigos",
        currency="MXN",
        groups=[
            Group(
                id="ana",
                name="Familia de Ana",
                representative="Ana",
                attendees=[
                    Attendee(id="a", name="Ana", categories=["food", "drinks", "general"]),
                    Attendee(id="b", name="Peque de Ana", categories=["food", "games", "general"]),
                ],
            ),
            Group(
                id="luis",
                name="Luis",
                representative="Luis",
                attendees=[
                    Attendee(id="c", name="Luis", categories=["food", "drinks", "general"]),
                ],
            ),
        ],
        expenses=[
            Expense(
                id="1",
                description="Comida para compartir",
                category="food",
                amount=60000,
                groupId="ana",
            ),
            Expense(
                id="2",
                description="Bebidas para brindar",
                category="drinks",
                amount=20000,
                groupId="luis",
            ),
            Expense(
                id="3",
                description="Actividad para peques",
                category="games",
                amount=10000,
                groupId="ana",
            ),
            Expense(
                id="4", description="Servilletas", category="general", amount=9000, groupId="luis"
            ),
        ],
    )


class EventStore:
    def __init__(self, seed: bool = True):
        self._lock = RLock()
        self._events: dict[str, Event] = {}
        if seed:
            self._events[SEED_EVENT_ID] = demo_event(SEED_EVENT_ID)

    def _get(self, event_id: str) -> Event:
        if event_id not in self._events:
            raise StoreError(404, "event_not_found", "No se encontró el evento.")
        return self._events[event_id]

    def get(self, event_id: str) -> Event:
        with self._lock:
            return self._get(event_id).model_copy(deep=True)

    def create(self, data: CreateEventRequest) -> Event:
        with self._lock:
            event = Event(id=str(uuid4()), **data.model_dump(), groups=[], expenses=[])
            self._events[event.id] = event
            return event.model_copy(deep=True)

    def create_demo(self) -> Event:
        with self._lock:
            event = demo_event(str(uuid4()))
            self._events[event.id] = event
            return event.model_copy(deep=True)

    def add_group(self, event_id: str, data: CreateGroupRequest) -> Event:
        with self._lock:
            event = self._get(event_id)
            attendees = [
                Attendee(
                    id=str(uuid4()),
                    name=a.name,
                    categories=list(dict.fromkeys([*a.categories, "general"])),
                )
                for a in data.attendees
            ]
            event.groups.append(
                Group(
                    id=str(uuid4()),
                    name=data.name,
                    representative=data.representative,
                    attendees=attendees,
                )
            )
            return event.model_copy(deep=True)

    def add_expense(self, event_id: str, data: CreateExpenseRequest) -> Event:
        with self._lock:
            event = self._get(event_id)
            if not any(g.id == data.groupId for g in event.groups):
                raise StoreError(422, "validation_error", "El grupo no pertenece a este evento.")
            if sum(e.amount for e in event.expenses) + data.amount > MAX_SAFE_INTEGER:
                raise StoreError(422, "validation_error", "El total excede el límite permitido.")
            event.expenses.append(Expense(id=str(uuid4()), **data.model_dump()))
            return event.model_copy(deep=True)
