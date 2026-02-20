import os

os.environ["GEOGAUGER_SKIP_BUILD"] = "1"

import json
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base
from app.osm_builder import (
    DATA_DIR,
    DEFAULT_REGIONS,
    get_regions,
    populate_db,
)

TEST_DATABASE_URL = "sqlite:///test_osm_builder.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


def test_get_regions_default():
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("GEOGAUGER_REGIONS", None)
        regions = get_regions()
        assert regions == DEFAULT_REGIONS


def test_get_regions_from_env():
    custom = [{"url": "https://example.com/test.osm.pbf", "country": "XX", "state": "Test"}]
    with patch.dict(os.environ, {"GEOGAUGER_REGIONS": json.dumps(custom)}):
        regions = get_regions()
        assert regions == custom


@patch("app.osm_builder.SessionLocal")
def test_populate_db(mock_session_local):
    mock_session = MagicMock()
    mock_session_local.return_value = mock_session

    streets = {
        "Main Street": (39.0, -75.5),
        "Oak Avenue": (39.1, -75.4),
    }
    count = populate_db(streets, "US", "Delaware")
    assert count == 2
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.close.assert_called_once()


@patch("app.osm_builder.SessionLocal")
def test_populate_db_empty(mock_session_local):
    count = populate_db({}, "US", "Delaware")
    assert count == 0
    mock_session_local.assert_not_called()


def test_data_dir_path():
    assert DATA_DIR.name == "data"
    assert DATA_DIR.parent.name == "backend"
