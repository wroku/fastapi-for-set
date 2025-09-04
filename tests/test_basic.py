import pytest
import sys

sys.path.append("/home/wroku/Dev/fastapi-for-set")
from fastapi.testclient import TestClient
from app.main import app
from .conftest import setup_db


app.user_middleware.clear()
app.middleware_stack = app.build_middleware_stack()
client = TestClient(app)


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"msg": "This is simple API for SET game leaderboard"}


def test_record_creation_and_retrieval(setup_db):
    new_record_data: dict = {"player": "Anonym", "score": 9, "time": 75.3}
    response = client.post("/records/", json=new_record_data)
    id = response.json().get('key')

    assert response.status_code == 200
    assert len(id) == 36

    response = client.get("/records/")
    assert new_record_data in response.json()


def test_record_update(setup_db):
    new_record_data: dict = {"player": "Anonym", "score": 9, "time": 75.3}
    response = client.post("/records/", json=new_record_data)
    id: str = response.json().get('key')

    updated_record_data: dict = {"player": "Chosen Name", "score": 12, "time": 103.5}
    response = client.put(f"/records/{id}", json=updated_record_data)

    assert response.status_code == 200
    assert updated_record_data == response.json()


@pytest.mark.parametrize('update_data', [{"player": "Another Name", "score": 9, "time": 78.3},
                                         {"player": "Chosen Name", "score": 12, "time": 16.3},
                                         {"player": "Chosen Name", "score": 13, "time": 90.3},
                                         {"player": "Chosen Name", "score": 13, "time": 90.3}])
def test_invalid_record_update(setup_db, update_data):
    new_record_data: dict = {"player": "Chosen Name", "score": 9, "time": 75.3}
    response = client.post("/records/", json=new_record_data)
    id: str = response.json().get('key')

    response = client.put(f"/records/{id}", json=update_data)

    assert response.status_code == 400
    assert response.json() == {"details": "Invalid update."}

