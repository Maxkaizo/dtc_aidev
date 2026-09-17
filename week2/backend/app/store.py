"""Transactional event repository backed by SQLAlchemy."""

from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from .database import Database
from .db_models import AttendeeRow, EventRow, ExpenseRow, GroupRow
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
    def __init__(self, database: Database):
        self.database = database

    def seed(self):
        try:
            with self.database.sessions.begin() as session:
                self._insert(session, demo_event(SEED_EVENT_ID))
        except IntegrityError:
            # A unique event ID makes seeding idempotent, including concurrent starts.
            with self.database.sessions() as session:
                if session.get(EventRow, SEED_EVENT_ID) is None:
                    raise

    def _insert(self, session, event: Event):
        session.add(EventRow(id=event.id, name=event.name, currency=event.currency))
        session.flush()
        for position, group in enumerate(event.groups):
            self._insert_group(session, event.id, group, position)
        for position, expense in enumerate(event.expenses):
            session.add(
                ExpenseRow(
                    event_id=event.id,
                    id=expense.id,
                    description=expense.description,
                    amount=expense.amount,
                    category=expense.category,
                    group_id=expense.groupId,
                    position=position,
                )
            )
        session.flush()

    def _insert_group(self, session, event_id: str, group: Group, position: int):
        session.add(
            GroupRow(
                event_id=event_id,
                id=group.id,
                name=group.name,
                representative=group.representative,
                position=position,
            )
        )
        session.flush()
        for index, attendee in enumerate(group.attendees):
            session.add(
                AttendeeRow(
                    event_id=event_id,
                    id=attendee.id,
                    group_id=group.id,
                    name=attendee.name,
                    categories=attendee.categories,
                    position=index,
                )
            )
        session.flush()

    def _read(self, session, event_id: str) -> Event:
        # Row-locking databases keep all component reads consistent with writers.
        # SQLite ignores FOR UPDATE and uses its explicit transaction snapshot.
        row = session.scalar(select(EventRow).where(EventRow.id == event_id).with_for_update())
        if row is None:
            raise StoreError(404, "event_not_found", "No se encontró el evento.")
        groups = session.scalars(
            select(GroupRow).where(GroupRow.event_id == event_id).order_by(GroupRow.position)
        ).all()
        attendees = session.scalars(
            select(AttendeeRow)
            .where(AttendeeRow.event_id == event_id)
            .order_by(AttendeeRow.position)
        ).all()
        expenses = session.scalars(
            select(ExpenseRow).where(ExpenseRow.event_id == event_id).order_by(ExpenseRow.position)
        ).all()
        return Event(
            id=row.id,
            name=row.name,
            currency=row.currency,
            groups=[
                Group(
                    id=g.id,
                    name=g.name,
                    representative=g.representative,
                    attendees=[
                        Attendee(id=a.id, name=a.name, categories=a.categories)
                        for a in attendees
                        if a.group_id == g.id
                    ],
                )
                for g in groups
            ],
            expenses=[
                Expense(
                    id=e.id,
                    description=e.description,
                    amount=e.amount,
                    category=e.category,
                    groupId=e.group_id,
                )
                for e in expenses
            ],
        )

    def _lock(self, session, event_id: str):
        # A real UPDATE serializes event writes on SQLite and row-locking databases.
        # Unlike SELECT FOR UPDATE alone, this also protects SQLite writes.
        result = session.execute(
            update(EventRow).where(EventRow.id == event_id).values(revision=EventRow.revision + 1)
        )
        if result.rowcount == 0:
            raise StoreError(404, "event_not_found", "No se encontró el evento.")

    def get(self, event_id: str) -> Event:
        with self.database.sessions.begin() as session:
            return self._read(session, event_id)

    def create(self, data: CreateEventRequest) -> Event:
        event = Event(id=str(uuid4()), **data.model_dump(), groups=[], expenses=[])
        with self.database.sessions.begin() as session:
            self._insert(session, event)
        return event

    def create_demo(self) -> Event:
        event = demo_event(str(uuid4()))
        with self.database.sessions.begin() as session:
            self._insert(session, event)
        return event

    def add_group(self, event_id: str, data: CreateGroupRequest) -> Event:
        with self.database.sessions.begin() as session:
            self._lock(session, event_id)
            event = self._read(session, event_id)
            attendees = [
                Attendee(
                    id=str(uuid4()),
                    name=a.name,
                    categories=list(dict.fromkeys([*a.categories, "general"])),
                )
                for a in data.attendees
            ]
            group = Group(
                id=str(uuid4()),
                name=data.name,
                representative=data.representative,
                attendees=attendees,
            )
            self._insert_group(session, event_id, group, len(event.groups))
            return self._read(session, event_id)

    def add_expense(self, event_id: str, data: CreateExpenseRequest) -> Event:
        with self.database.sessions.begin() as session:
            self._lock(session, event_id)
            event = self._read(session, event_id)
            if not any(g.id == data.groupId for g in event.groups):
                raise StoreError(422, "validation_error", "El grupo no pertenece a este evento.")
            if sum(e.amount for e in event.expenses) + data.amount > MAX_SAFE_INTEGER:
                raise StoreError(422, "validation_error", "El total excede el límite permitido.")
            session.add(
                ExpenseRow(
                    event_id=event_id,
                    id=str(uuid4()),
                    description=data.description,
                    amount=data.amount,
                    category=data.category,
                    group_id=data.groupId,
                    position=len(event.expenses),
                )
            )
            session.flush()
            return self._read(session, event_id)
