import os

os.environ["GEOGAUGER_SKIP_BUILD"] = "1"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.models import Base, get_db

TEST_DATABASE_URL = "sqlite:///test_geogauger.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_add_street():
    street = {
        "street_name": "Main Street",
        "city": "Springfield",
        "state": "IL",
        "country": "US",
        "latitude": 39.7817,
        "longitude": -89.6501,
    }
    response = client.post("/api/streets", json=street)
    assert response.status_code == 200
    data = response.json()
    assert data["street_name"] == "Main Street"
    assert data["city"] == "Springfield"
    assert "id" in data


def test_add_street_without_city():
    street = {
        "street_name": "Highway 1",
        "country": "US",
        "state": "DE",
        "latitude": 39.0,
        "longitude": -75.5,
    }
    response = client.post("/api/streets", json=street)
    assert response.status_code == 200
    data = response.json()
    assert data["street_name"] == "Highway 1"
    assert data["city"] is None


def test_list_streets():
    street = {
        "street_name": "Oak Avenue",
        "city": "Portland",
        "state": "OR",
        "country": "US",
        "latitude": 45.5152,
        "longitude": -122.6784,
    }
    client.post("/api/streets", json=street)
    response = client.get("/api/streets")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


def test_locate_no_streets():
    response = client.post("/api/locate", json={"street_names": []})
    assert response.status_code == 200
    assert response.json() == []


def test_locate_with_matches():
    streets = [
        {
            "street_name": "Elm Street",
            "city": "Austin",
            "state": "TX",
            "country": "US",
            "latitude": 30.2672,
            "longitude": -97.7431,
        },
        {
            "street_name": "Pine Road",
            "city": "Austin",
            "state": "TX",
            "country": "US",
            "latitude": 30.2700,
            "longitude": -97.7400,
        },
    ]
    for s in streets:
        client.post("/api/streets", json=s)

    response = client.post("/api/locate", json={"street_names": ["Elm Street", "Pine Road"]})
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["city"] == "Austin"
    assert data[0]["match_count"] == 2


def test_locate_without_city():
    streets = [
        {
            "street_name": "Market Street",
            "state": "Delaware",
            "country": "US",
            "latitude": 39.74,
            "longitude": -75.55,
        },
        {
            "street_name": "King Street",
            "state": "Delaware",
            "country": "US",
            "latitude": 39.75,
            "longitude": -75.54,
        },
    ]
    for s in streets:
        client.post("/api/streets", json=s)

    response = client.post(
        "/api/locate", json={"street_names": ["Market Street", "King Street"]}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["state"] == "Delaware"
    assert data[0]["match_count"] == 2
