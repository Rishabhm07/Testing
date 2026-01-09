from flask import Flask, request, jsonify
import json
import uuid
from functools import wraps
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "db.json")

def read_db():
    with open(DB_FILE, "r") as f:
        return json.load(f)


app = Flask(__name__)

DB_FILE = os.environ.get("DB_FILE", "db.json")

SESSIONS = {}   # token storage


# ---------- Utility Functions ----------
def read_db():
    with open(DB_FILE, "r") as f:
        return json.load(f)


def write_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)


# ---------- Authentication Decorator ----------
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token or token not in SESSIONS:
            return jsonify({"message": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated


# ---------- Login ----------
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    db = read_db()

    for user in db["users"]:
        if user["username"] == username and user["password"] == password:
            token = str(uuid.uuid4())
            SESSIONS[token] = username
            return jsonify({"token": token})

    return jsonify({"message": "Invalid credentials"}), 401


# ---------- CREATE ----------

@app.route("/items", methods=["POST"])
@token_required
def create_item():
    item = request.json
    db = read_db()

    item["id"] = len(db["items"]) + 1
    db["items"].append(item)

    write_db(db)
    return jsonify(item), 201


# ---------- READ ALL ----------
@app.route("/items", methods=["GET"])
@token_required
def get_items():
    db = read_db()
    return jsonify(db["items"])


# ---------- READ ONE ----------
@app.route("/items/<int:item_id>", methods=["GET"])
@token_required
def get_item(item_id):
    db = read_db()
    for item in db["items"]:
        if item["id"] == item_id:
            return jsonify(item)
    return jsonify({"message": "Item not found"}), 404


# ---------- UPDATE ----------
@app.route("/items/<int:item_id>", methods=["PUT"])
@token_required
def update_item(item_id):
    data = request.json
    db = read_db()

    for item in db["items"]:
        if item["id"] == item_id:
            item.update(data)
            write_db(db)
            return jsonify(item)

    return jsonify({"message": "Item not found"}), 404


# ---------- DELETE ----------
@app.route("/items/<int:item_id>", methods=["DELETE"])
@token_required
def delete_item(item_id):
    db = read_db()
    items = db["items"]

    for item in items:
        if item["id"] == item_id:
            items.remove(item)
            write_db(db)
            return jsonify({"message": "Item deleted"})

    return jsonify({"message": "Item not found"}), 404


# ---------- Run Server ----------
if __name__ == "__main__":
    app.run(debug=True)


