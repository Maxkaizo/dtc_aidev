from pathlib import Path

import yaml
from jsonschema import Draft202012Validator
from openapi_spec_validator import validate

SPEC = yaml.safe_load((Path(__file__).resolve().parents[2] / "openapi.yaml").read_text())


def assert_schema(name, data):
    schema = dict(SPEC["components"]["schemas"][name], components=SPEC["components"])
    Draft202012Validator(schema).validate(data)


def test_openapi_documents_and_route_coverage(client):
    validate(SPEC)
    generated = client.get("/openapi.json").json()
    validate(generated)
    for path, item in SPEC["paths"].items():
        for method, operation in item.items():
            if method not in {"get", "post"}:
                continue
            actual = generated["paths"]["/api" + path][method]
            assert actual["operationId"] == operation["operationId"]
            assert actual.get("security", []) == operation["security"]
            assert set(operation["responses"]) <= set(actual["responses"])
    assert client.get("/docs").status_code == 200


def test_every_success_response_matches_contract(client):
    seed = client.get("/api/events/demo").json()
    expected = SPEC["components"]["examples"]["DemoEvent"]["value"]
    assert {**seed, "id": expected["id"]} == expected
    assert_schema("Event", seed)
    assert_schema("Event", client.post("/api/events/demo").json())
    event = client.post("/api/events", json={"name": "Test", "currency": "MXN"}).json()
    assert_schema("Event", event)
    path = "/api/events/" + event["id"]
    event = client.post(
        path + "/groups",
        json={
            "name": "A",
            "representative": "A",
            "attendees": [{"name": "A", "categories": []}],
        },
    ).json()
    assert_schema("Event", event)
    event = client.post(
        path + "/expenses",
        json={
            "description": "X",
            "amount": 123,
            "category": "general",
            "groupId": event["groups"][0]["id"],
        },
    ).json()
    assert_schema("Event", event)
    assert_schema("Event", client.get(path).json())
    credentials = {"username": "tester", "password": "strong password"}
    assert_schema("User", client.post("/api/auth/register", json=credentials).json())
    token = client.post("/api/auth/login", json=credentials).json()
    assert_schema("Token", token)
    assert_schema(
        "User",
        client.get(
            "/api/auth/me",
            headers={
                "Authorization": "Bearer " + token["access_token"],
            },
        ).json(),
    )
    assert_schema("Error", client.get("/api/events/missing").json())
    assert_schema("Error", client.get("/api/auth/me").json())
