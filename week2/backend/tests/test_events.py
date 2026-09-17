from concurrent.futures import ThreadPoolExecutor

import pytest

from app.models import CreateExpenseRequest
from app.store import MAX_SAFE_INTEGER, EventStore


def test_seed_and_independent_demos(client):
    seed = client.get("/api/events/demo")
    assert seed.status_code == 200
    event = seed.json()
    assert sum(e["amount"] for e in event["expenses"]) == 99000
    assert [g["id"] for g in event["groups"]] == ["ana", "luis"]
    a = client.post("/api/events/demo")
    b = client.post("/api/events/demo")
    assert a.status_code == b.status_code == 201
    assert len({a.json()["id"], b.json()["id"], event["id"]}) == 3
    assert client.get("/api/events/" + a.json()["id"]).json() == a.json()


def test_full_workflow_preserves_order_and_category_rules(client):
    created = client.post("/api/events", json={"name": "  Picnic  ", "currency": "EUR"})
    assert created.status_code == 201
    event = created.json()
    assert event["name"] == "Picnic" and event["groups"] == event["expenses"] == []
    url = "/api/events/" + event["id"]
    group = {
        "name": " A ",
        "representative": " Ana ",
        "attendees": [
            {"name": " First ", "categories": ["games", "games"]},
            {"name": "Second", "categories": []},
        ],
    }
    result = client.post(url + "/groups", json=group)
    assert result.status_code == 201
    added = result.json()["groups"][0]
    assert added["name"] == "A" and added["representative"] == "Ana"
    assert [a["name"] for a in added["attendees"]] == ["First", "Second"]
    assert added["attendees"][0]["categories"] == ["games", "general"]
    assert added["attendees"][1]["categories"] == ["general"]
    assert len({a["id"] for a in added["attendees"]}) == 2
    # Representative is not silently added, and categories without members are valid expenses.
    expense = {"description": " Food ", "amount": 101, "category": "food", "groupId": added["id"]}
    result = client.post(url + "/expenses", json=expense)
    assert result.status_code == 201
    assert result.json()["expenses"][0]["description"] == "Food"
    assert result.json()["groups"] == [added]
    assert client.get(url).json() == result.json()
    second = client.post(url + "/groups", json=group).json()
    assert second["groups"][0] == added
    assert second["groups"][1]["id"] != added["id"]


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"name": " ", "currency": "MXN"},
        {"name": "X", "currency": "GBP"},
        {"name": "x" * 101, "currency": "MXN"},
        {"name": "X", "currency": "USD", "extra": 1},
        {"name": 3, "currency": "MXN"},
    ],
)
def test_invalid_event(client, body):
    response = client.post("/api/events", json=body)
    assert response.status_code == 422
    assert response.json() == {"code": "validation_error", "message": "Revisa los datos enviados."}


@pytest.mark.parametrize("amount", [0, -1, 1.2, True, "100", 10_000_000_001, None])
def test_invalid_amount_is_atomic(client, amount):
    before = client.get("/api/events/demo").json()
    response = client.post(
        "/api/events/demo/expenses",
        json={
            "description": "Test",
            "amount": amount,
            "category": "food",
            "groupId": "ana",
        },
    )
    assert response.status_code == 422
    assert client.get("/api/events/demo").json() == before


@pytest.mark.parametrize(
    "changes",
    [
        {"attendees": []},
        {"representative": " "},
        {"attendees": [{"name": "A", "categories": ["unknown"]}]},
        {"attendees": [{"name": " ", "categories": []}]},
    ],
)
def test_invalid_group_is_atomic(client, changes):
    before = client.get("/api/events/demo").json()
    body = {"name": "A", "representative": "A", "attendees": [{"name": "A", "categories": []}]}
    body.update(changes)
    assert client.post("/api/events/demo/groups", json=body).status_code == 422
    assert client.get("/api/events/demo").json() == before


def test_missing_event_and_foreign_group(client):
    assert client.get("/api/events/missing").status_code == 404
    group = {"name": "A", "representative": "A", "attendees": [{"name": "A", "categories": []}]}
    response = client.post("/api/events/missing/groups", json=group)
    assert response.status_code == 404 and response.json()["code"] == "event_not_found"
    expense = {"description": "X", "amount": 1, "category": "food", "groupId": "ana"}
    assert client.post("/api/events/missing/expenses", json=expense).status_code == 404
    empty = client.post("/api/events", json={"name": "X", "currency": "USD"}).json()
    response = client.post(f"/api/events/{empty['id']}/expenses", json=expense)
    assert response.status_code == 422
    assert client.get(f"/api/events/{empty['id']}").json()["expenses"] == []


def test_total_overflow_is_atomic(client):
    # Inject a near-limit fixture without allocating 900,000 expense records.
    event = client.app.state.store._events["demo"]
    event.expenses = [event.expenses[0].model_copy(update={"amount": MAX_SAFE_INTEGER - 1})]
    expense = {"description": "X", "amount": 2, "category": "food", "groupId": "ana"}
    response = client.post("/api/events/demo/expenses", json=expense)
    assert response.status_code == 422
    assert len(event.expenses) == 1


def test_concurrent_writes_and_detached_snapshots():
    store = EventStore()
    expense = CreateExpenseRequest(description="X", amount=1, category="general", groupId="ana")
    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(lambda _: store.add_expense("demo", expense), range(40)))
    snapshot = store.get("demo")
    assert len(snapshot.expenses) == 44
    assert len({e.id for e in snapshot.expenses}) == 44
    snapshot.groups.clear()
    assert len(store.get("demo").groups) == 2


def test_validation_errors_and_cors(client):
    assert (
        client.post(
            "/api/events", content="{", headers={"Content-Type": "application/json"}
        ).status_code
        == 422
    )
    response = client.options(
        "/api/events",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    response = client.options(
        "/api/events",
        headers={
            "Origin": "https://unknown.example",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert "access-control-allow-origin" not in response.headers
