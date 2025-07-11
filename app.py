from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
from datetime import datetime, timedelta
import os

app = Flask(__name__)
# Разрешаваме CORS само за фронт-енд домейна
CORS(app, resources={
    r"/*": {"origins": "https://wng.yanisworkshop.com"}
})

DB_PATH = "chests.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_monday():
    today = datetime.today()
    monday = today - timedelta(days=today.weekday())
    return monday.strftime('%Y-%m-%d')

def get_total_chests():
    monday = get_monday()
    conn = get_db_connection()
    data = conn.execute(
        "SELECT chest_type, SUM(count) as total FROM chests "
        "WHERE date >= ? GROUP BY chest_type ORDER BY total DESC",
        (monday,)
    ).fetchall()
    conn.close()
    return {row["chest_type"]: row["total"] for row in data}

@app.route("/")
def index():
    return jsonify({"status": "ChestTracker API is running"}), 200

@app.route("/summary")
def summary():
    monday = get_monday()
    conn = get_db_connection()
    data = conn.execute(
        "SELECT players.name, SUM(chests.count) as total FROM chests "
        "JOIN players ON chests.player_id = players._
