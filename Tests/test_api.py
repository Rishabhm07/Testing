import json
import os
import tempfile
import pytest
from App import app

@pytest.fixture
def client():
    # Create temp DB file
    db_fd, db_path = tempfile.mkstemp()

    with open(db_path, "w") as f:
        json.dump({
            "users": [{"username": "admin", "password": "admin123"}],
            "items": []
        }, f)

    os.environ["DB_FILE"] = db_path

    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

    os.close(db_fd)
    os.unlink(db_path)


def login(client):
    response = client.post(
        "/login",
        json={"username": "admin", "password": "admin123"}
    )
    return response.get_json()["token"]


# ------------------ TESTS ------------------

def test_login_success(client):
    response = client.post(
        "/login",
        json={"username": "admin", "password": "admin123"}
    )
    assert response.status_code == 200
    assert "token" in response.get_json()


def test_login_failure(client):
    response = client.post(
        "/login",
        json={"username": "admin", "password": "wrong"}
    )
    assert response.status_code == 401


def test_create_item(client):
    token = login(client)

    response = client.post(
        "/items",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Laptop", "price": 50000}
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data["name"] == "Laptop"


def test_get_items(client):
    token = login(client)

    client.post(
        "/items",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Mouse", "price": 500}
    )

    response = client.get(
        "/items",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert isinstance(response.get_json(), list)


def test_update_item(client):
    token = login(client)

    client.post(
        "/items",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Keyboard", "price": 1200}
    )

    response = client.put(
        "/items/1",
        headers={"Authorization": f"Bearer {token}"},
        json={"price": 1000}
    )

    assert response.status_code == 200
    assert response.get_json()["price"] == 1000


def test_delete_item(client):
    token = login(client)

    client.post(
        "/items",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Monitor", "price": 12000}
    )

    response = client.delete(
        "/items/1",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200


def test_unauthorized_access(client):
    response = client.get("/items")
    assert response.status_code == 401
