from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)  # 🔥 Това добавя CORS за всички маршрути

DB_PATH = "chests.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_monday():
    today = datetime.today()
    monday = today - timedelta(days=today.weekday())
    return monday.strftime('%Y-%m-%d')

@app.route("/")
def index():
    return jsonify({"status": "ChestTracker API is running"}), 200

@app.route("/summary")
def summary():
    monday = get_monday()
    conn = get_db_connection()
    data = conn.execute(
        "SELECT players.name, SUM(chests.count) as total FROM chests "
        "JOIN players ON chests.player_id = players.id "
        "WHERE chests.date >= ? "
        "GROUP BY players.name ORDER BY total DESC", (monday,)
    ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in data])

@app.route("/player/<name>")
def player(name):
    monday = get_monday()
    conn = get_db_connection()
    player = conn.execute("SELECT id FROM players WHERE name = ?", (name,)).fetchone()
    if not player:
        conn.close()
        return jsonify({"error": "Player not found"}), 404
    chests = conn.execute(
        "SELECT chest_type, SUM(count) as total FROM chests "
        "WHERE player_id = ? AND date >= ? GROUP BY chest_type ORDER BY total DESC",
        (player["id"], monday)
    ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in chests])

@app.route("/update", methods=["POST"])
def update():
    data = request.get_json()
    if not data or "player" not in data or "chests" not in data:
        return jsonify({"error": "Invalid data"}), 400

    player_name = data["player"]
    chests_data = data["chests"]
    today = datetime.today().strftime('%Y-%m-%d')

    conn = get_db_connection()
    player = conn.execute("SELECT id FROM players WHERE name = ?", (player_name,)).fetchone()
    if not player:
        conn.execute("INSERT INTO players (name) VALUES (?)", (player_name,))
        conn.commit()
        player_id = conn.execute("SELECT id FROM players WHERE name = ?", (player_name,)).fetchone()["id"]
    else:
        player_id = player["id"]

    for chest_type, count in chests_data.items():
        conn.execute(
            "INSERT INTO chests (player_id, chest_type, count, date) VALUES (?, ?, ?, ?)",
            (player_id, chest_type, count, today)
        )
    conn.commit()
    conn.close()
    return jsonify({"status": "OK"}), 200

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
