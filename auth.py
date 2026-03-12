import datetime
import hashlib
import random
import string
import json
import os
import time
import sys
from ui import *
from utils import *
from storage import *


if sys.platform == "win32":
    os.system("")

### login 
def login():
    global current_user, current_role
    clear_screen()
    header("E-VOTING SYSTEM", THEME_LOGIN)
    print()
    menu_item(1, "Login as Admin", THEME_LOGIN)
    menu_item(2, "Login as Voter", THEME_LOGIN)
    menu_item(3, "Register as Voter", THEME_LOGIN)
    menu_item(4, "Exit", THEME_LOGIN)
    print()
    choice = prompt("Enter choice: ")

    if choice == "1":
        clear_screen()
        header("ADMIN LOGIN", THEME_ADMIN)
        print()
        username = prompt("Username: ")
        password = masked_input("Password: ").strip()
        hashed = hash_password(password)
        found = False
        for aid, admin in admins.items():
            if admin["username"] == username and admin["password"] == hashed:
                if not admin["is_active"]:
                    error("This account has been deactivated.")
                    log_action("LOGIN_FAILED", username, "Account deactivated")
                    pause()
                    return False
                current_user = admin
                current_role = "admin"
                found = True
                log_action("LOGIN", username, "Admin login successful")
                print()
                success(f"Welcome, {admin['full_name']}!")
                pause()
                return admin, "admin"
        if not found:
            error("Invalid credentials.")
            log_action("LOGIN_FAILED", username, "Invalid admin credentials")
            pause()
            return False, None, None

    elif choice == "2":
        clear_screen()
        header("VOTER LOGIN", THEME_VOTER)
        print()
        voter_card = prompt("Voter Card Number: ")
        password = masked_input("Password: ").strip()
        hashed = hash_password(password)
        found = False, None, None
        for vid, voter in voters.items():
            if voter["voter_card_number"] == voter_card and voter["password"] == hashed:
                if not voter["is_active"]:
                    error("This voter account has been deactivated.")
                    log_action("LOGIN_FAILED", voter_card, "Voter account deactivated")
                    pause()
                    return False
                if not voter["is_verified"]:
                    warning("Your voter registration has not been verified yet.")
                    info("Please contact an admin to verify your registration.")
                    log_action("LOGIN_FAILED", voter_card, "Voter not verified")
                    pause()
                    return False, None, None
                current_user = voter
                current_role = "voter"
                found = True
                log_action("LOGIN", voter_card, "Voter login successful")
                print()
                success(f"Welcome, {voter['full_name']}!")
                pause()
                return voter, "voter"
        if not found:
            error("Invalid voter card number or password.")
            log_action("LOGIN_FAILED", voter_card, "Invalid voter credentials")
            pause()
            return False, None, None

    elif choice == "3":
        register_voter()
        return False, None, None
    elif choice == "4":
        print()
        info("Goodbye!")
        save_data()
        exit()
    else:
        error("Invalid choice.")
        pause()
        return False, None, None

def register_voter():
    global voter_id_counter
    clear_screen()
    header("VOTER REGISTRATION", THEME_VOTER)
    print()
    full_name = prompt("Full Name: ")
    if not full_name:
        error("Name cannot be empty.")
        pause()
        return
    national_id = prompt("National ID Number: ")
    if not national_id:
        error("National ID cannot be empty.")
        pause()
        return
    for vid, v in voters.items():
        if v["national_id"] == national_id:
            error("A voter with this National ID already exists.")
            pause()
            return
    dob_str = prompt("Date of Birth (YYYY-MM-DD): ")
    try:
        dob = datetime.datetime.strptime(dob_str, "%Y-%m-%d")
        age = (datetime.datetime.now() - dob).days // 365
        if age < MIN_VOTER_AGE:
            error(f"You must be at least {MIN_VOTER_AGE} years old to register.")
            pause()
            return
    except ValueError:
        error("Invalid date format.")
        pause()
        return
    gender = prompt("Gender (M/F/Other): ").upper()
    if gender not in ["M", "F", "OTHER"]:
        error("Invalid gender selection.")
        pause()
        return
    address = prompt("Residential Address: ")
    phone = prompt("Phone Number: ")
    email = prompt("Email Address: ")
    password = masked_input("Create Password: ").strip()
    if len(password) < 6:
        error("Password must be at least 6 characters.")
        pause()
        return
    confirm_password = masked_input("Confirm Password: ").strip()
    if password != confirm_password:
        error("Passwords do not match.")
        pause()
        return
    if not voting_stations:
        error("No voting stations available. Contact admin.")
        pause()
        return
    subheader("Available Voting Stations", THEME_VOTER)
    for sid, station in voting_stations.items():
        if station["is_active"]:
            print(f"    {BRIGHT_BLUE}{sid}.{RESET} {station['name']} {DIM}- {station['location']}{RESET}")
    try:
        station_choice = int(prompt("\nSelect your voting station ID: "))
        if station_choice not in voting_stations or not voting_stations[station_choice]["is_active"]:
            error("Invalid station selection.")
            pause()
            return
    except ValueError:
        error("Invalid input.")
        pause()
        return
    voter_card = generate_voter_card_number()
    voters[voter_id_counter] = {
        "id": voter_id_counter, "full_name": full_name, "national_id": national_id,
        "date_of_birth": dob_str, "age": age, "gender": gender, "address": address,
        "phone": phone, "email": email, "password": hash_password(password),
        "voter_card_number": voter_card, "station_id": station_choice,
        "is_verified": False, "is_active": True, "has_voted_in": [],
        "registered_at": str(datetime.datetime.now()), "role": "voter"
    }
    log_action("REGISTER", full_name, f"New voter registered with card: {voter_card}")
    print()
    success("Registration successful!")
    print(f"  {BOLD}Your Voter Card Number: {BRIGHT_YELLOW}{voter_card}{RESET}")
    warning("IMPORTANT: Save this number! You need it to login.")
    info("Your registration is pending admin verification.")
    voter_id_counter += 1
    save_data()
    pause()
