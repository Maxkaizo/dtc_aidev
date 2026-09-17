import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(database_url=f"sqlite:///{tmp_path / 'test.db'}")) as client:
        yield client
