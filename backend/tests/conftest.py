import os

os.environ["DATABASE_URL"] = "sqlite:///./.cache/test-import.db"
os.environ["MOCK_MODE"] = "true"
os.environ["MODEL_API_KEY"] = ""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from app.db import Base, get_session, make_engine
from app.main import app


@pytest.fixture
def db(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    with factory() as session:
        yield session
    engine.dispose()


@pytest.fixture
def client(db):
    def override():
        yield db

    app.dependency_overrides[get_session] = override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def star(client):
    response = client.post(
        "/api/stars",
        json={
            "title": "深海的微光",
            "original_text": "我想了解海洋和深海生物。",
            "description": "深海生物的发光现象",
            "category": "自然",
            "tags": ["海洋", "深海"],
        },
    )
    assert response.status_code == 201
    return response.json()


def proposal_run(client, key=None):
    response = client.post(
        "/api/agent/runs",
        json={
            "request_type": "explore",
            "text": "海洋",
            "available_minutes": 10,
            "budget": 0,
            "energy_level": "low",
        },
        headers={"Idempotency-Key": key} if key else {},
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture
def quest(client, star):
    run = proposal_run(client)
    result = client.post(f"/api/agent/runs/{run['run_id']}/decision", json={"approved": True})
    assert result.status_code == 200, result.text
    return result.json()["quest_id"]
