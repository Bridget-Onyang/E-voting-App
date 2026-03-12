import datetime
import hashlib
import random
import string
import json
import os
import time
import sys
import ui
from ui import info, error

if sys.platform == "win32":
    os.system("")

### Data storage
candidates = {}
candidate_id_counter = 1
voting_stations = {}
station_id_counter = 1
polls = {}
poll_id_counter = 1
positions = {}
position_id_counter = 1
voters = {}
voter_id_counter = 1
admins = {}
admin_id_counter = 1
votes = []
audit_log = []
current_user = None
current_role = None

MIN_CANDIDATE_AGE = 25
MAX_CANDIDATE_AGE = 75
REQUIRED_EDUCATION_LEVELS = ["Bachelor's Degree", "Master's Degree", "PhD", "Doctorate"]
MIN_VOTER_AGE = 18

admins[1] = {
    "id": 1, "username": "admin",
    "password": hashlib.sha256("admin123".encode()).hexdigest(),
    "full_name": "System Administrator", "email": "admin@evote.com",
    "role": "super_admin", "created_at": str(datetime.datetime.now()), "is_active": True
}
admin_id_counter = 2

def save_data():
    data = {
        "candidates": candidates, "candidate_id_counter": candidate_id_counter,
        "voting_stations": voting_stations, "station_id_counter": station_id_counter,
        "polls": polls, "poll_id_counter": poll_id_counter,
        "positions": positions, "position_id_counter": position_id_counter,
        "voters": voters, "voter_id_counter": voter_id_counter,
        "admins": admins, "admin_id_counter": admin_id_counter,
        "votes": votes, "audit_log": audit_log
    }
    try:
        with open("evoting_data.json", "w") as f:
            json.dump(data, f, indent=2)
        info("Data saved successfully")
    except Exception as e:
        error(f"Error saving data: {e}")

def load_data():
    global candidates, candidate_id_counter, voting_stations, station_id_counter
    global polls, poll_id_counter, positions, position_id_counter
    global voters, voter_id_counter, admins, admin_id_counter, votes, audit_log
    try:
        if os.path.exists("evoting_data.json"):
            with open("evoting_data.json", "r") as f:
                data = json.load(f)
            candidates = {int(k): v for k, v in data.get("candidates", {}).items()}
            candidate_id_counter = data.get("candidate_id_counter", 1)
            voting_stations = {int(k): v for k, v in data.get("voting_stations", {}).items()}
            station_id_counter = data.get("station_id_counter", 1)
            polls = {int(k): v for k, v in data.get("polls", {}).items()}
            poll_id_counter = data.get("poll_id_counter", 1)
            positions = {int(k): v for k, v in data.get("positions", {}).items()}
            position_id_counter = data.get("position_id_counter", 1)
            voters = {int(k): v for k, v in data.get("voters", {}).items()}
            voter_id_counter = data.get("voter_id_counter", 1)
            admins = {int(k): v for k, v in data.get("admins", {}).items()}
            admin_id_counter = data.get("admin_id_counter", 1)
            votes = data.get("votes", [])
            audit_log = data.get("audit_log", [])
            info("Data loaded successfully")
    except Exception as e:
        error(f"Error loading data: {e}")