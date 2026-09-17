from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import IntegrityError
from sqlalchemy.schema import CreateTable

from app.database import Database
from app.db_models import Base, EventRow, ExpenseRow
from app.main import create_app
from app.models import CreateExpenseRequest, CreateGroupRequest
from app.store import EventStore, StoreError


def test_events_persist_and_seed_does_not_overwrite(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'persistent.db'}"
    monkeypatch.setenv("DATABASE_URL", url)
    group = {
        "name": "New",
        "representative": "A",
        "attendees": [
            {"name": "First", "categories": ["games", "food"]},
            {"name": "Second", "categories": []},
        ],
    }
    with TestClient(create_app()) as client:
        created = client.post("/api/events", json={"name": "Saved", "currency": "EUR"}).json()
        path = "/api/events/" + created["id"]
        event = client.post(path + "/groups", json=group).json()
        event = client.post(
            path + "/expenses",
            json={
                "description": "Games",
                "category": "games",
                "amount": 101,
                "groupId": event["groups"][0]["id"],
            },
        ).json()
        seed = client.post("/api/events/demo/groups", json=group).json()
    with TestClient(create_app()) as client:
        assert client.get(path).json() == event
        assert client.get("/api/events/demo").json() == seed
        with client.app.state.database.sessions() as session:
            assert session.scalar(select(func.count()).select_from(EventRow)) == 2


def test_event_scoped_demo_ids_and_foreign_keys(client):
    a = client.post("/api/events/demo").json()
    b = client.post("/api/events/demo").json()
    assert a["id"] != b["id"]
    assert a["groups"][0]["id"] == b["groups"][0]["id"] == "ana"
    empty = client.post("/api/events", json={"name": "Empty", "currency": "MXN"}).json()
    with pytest.raises(IntegrityError), client.app.state.database.sessions.begin() as session:
        session.add(
            ExpenseRow(
                event_id=empty["id"],
                id="invalid",
                group_id="ana",
                description="Wrong event",
                amount=1,
                category="food",
                position=0,
            )
        )
    assert client.get("/api/events/" + empty["id"]).json()["expenses"] == []


def test_two_engines_serialize_writes_and_preserve_order(tmp_path):
    url = f"sqlite:///{tmp_path / 'shared.db'}"
    databases = [Database(url), Database(url)]
    databases[0].initialize()
    stores = [EventStore(db) for db in databases]
    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            list(executor.map(lambda store: store.seed(), stores))
        group = CreateGroupRequest(
            name="A",
            representative="A",
            attendees=[
                {"name": "First", "categories": []},
                {"name": "Second", "categories": ["food"]},
            ],
        )
        with ThreadPoolExecutor(max_workers=8) as executor:
            list(executor.map(lambda n: stores[n % 2].add_group("demo", group), range(20)))
        snapshot = stores[0].get("demo")
        assert len(snapshot.groups) == 22
        assert len({g.id for g in snapshot.groups}) == 22
        assert stores[1].get("demo") == snapshot
        for g in snapshot.groups[2:]:
            assert [a.name for a in g.attendees] == ["First", "Second"]
    finally:
        for db in databases:
            db.close()


def test_concurrent_limit_check_rolls_back_rejected_write(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'limit.db'}"
    databases = [Database(url), Database(url)]
    databases[0].initialize()
    stores = [EventStore(db) for db in databases]
    stores[0].seed()
    monkeypatch.setattr("app.store.MAX_SAFE_INTEGER", 99001)
    expense = CreateExpenseRequest(description="Cent", amount=1, category="general", groupId="ana")

    def insert(store):
        try:
            store.add_expense("demo", expense)
            return "ok"
        except StoreError as error:
            return error.code

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(insert, stores))
        assert sorted(results) == ["ok", "validation_error"]
        event = stores[0].get("demo")
        assert sum(e.amount for e in event.expenses) == 99001
        assert len(event.expenses) == 5
    finally:
        for db in databases:
            db.close()


def test_portable_schema_compiles_for_postgres():
    # Compilation is a portability check, not a live Postgres integration test.
    for table in Base.metadata.sorted_tables:
        sql = str(CreateTable(table).compile(dialect=postgresql.dialect()))
        assert "CREATE TABLE" in sql
