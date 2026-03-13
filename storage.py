import datetime
import hashlib
import json
import os

from ui import error, info


DATA_FILE = os.path.join(os.path.dirname(__file__), "evoting_data.json")

# Data storage
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


def _seed_default_admin():
    global admin_id_counter
    if admins:
        return
    admins[1] = {
        "id": 1,
        "username": "admin",
        "password": hashlib.sha256("admin123".encode()).hexdigest(),
        "full_name": "System Administrator",
        "email": "admin@evote.com",
        "role": "super_admin",
        "created_at": str(datetime.datetime.now()),
        "is_active": True,
    }
    admin_id_counter = 2


def _to_int_key_dict(data):
    return {int(k): v for k, v in data.items()}


def _replace_dict_in_place(target, source):
    target.clear()
    target.update(source)


def _replace_list_in_place(target, source):
    target.clear()
    target.extend(source)


_seed_default_admin()


def save_data():
    data = {
        "candidates": candidates,
        "candidate_id_counter": candidate_id_counter,
        "voting_stations": voting_stations,
        "station_id_counter": station_id_counter,
        "polls": polls,
        "poll_id_counter": poll_id_counter,
        "positions": positions,
        "position_id_counter": position_id_counter,
        "voters": voters,
        "voter_id_counter": voter_id_counter,
        "admins": admins,
        "admin_id_counter": admin_id_counter,
        "votes": votes,
        "audit_log": audit_log,
    }
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as data_file:
            json.dump(data, data_file, indent=2)
        info("Data saved successfully")
    except OSError as exc:
        error(f"Error saving data: {exc}")


def load_data():
    global candidate_id_counter, station_id_counter, poll_id_counter
    global position_id_counter, voter_id_counter, admin_id_counter

    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as data_file:
                data = json.load(data_file)

            _replace_dict_in_place(candidates, _to_int_key_dict(data.get("candidates", {})))
            candidate_id_counter = data.get("candidate_id_counter", 1)

            _replace_dict_in_place(voting_stations, _to_int_key_dict(data.get("voting_stations", {})))
            station_id_counter = data.get("station_id_counter", 1)

            _replace_dict_in_place(polls, _to_int_key_dict(data.get("polls", {})))
            poll_id_counter = data.get("poll_id_counter", 1)

            _replace_dict_in_place(positions, _to_int_key_dict(data.get("positions", {})))
            position_id_counter = data.get("position_id_counter", 1)

            _replace_dict_in_place(voters, _to_int_key_dict(data.get("voters", {})))
            voter_id_counter = data.get("voter_id_counter", 1)

            _replace_dict_in_place(admins, _to_int_key_dict(data.get("admins", {})))
            admin_id_counter = data.get("admin_id_counter", 1)

            _replace_list_in_place(votes, data.get("votes", []))
            _replace_list_in_place(audit_log, data.get("audit_log", []))

            if not admins:
                _seed_default_admin()

            info("Data loaded successfully")
            return

        _seed_default_admin()
    except (OSError, json.JSONDecodeError) as exc:
        error(f"Error loading data: {exc}")
