import datetime

import storage
import ui
import utils


class AuthService:
    LOGIN_ADMIN_CHOICE = "1"
    LOGIN_VOTER_CHOICE = "2"
    REGISTER_VOTER_CHOICE = "3"
    EXIT_CHOICE = "4"
    MIN_PASSWORD_LENGTH = 6
    VALID_GENDERS = {"M", "F", "OTHER"}

    def _show_invalid_choice(self):
        ui.error("Invalid choice.")
        ui.pause()
        return None, None

    def _auth_menu_actions(self):
        return {
            self.LOGIN_ADMIN_CHOICE: self._login_admin,
            self.LOGIN_VOTER_CHOICE: self._login_voter,
        }

    @staticmethod
    def _is_valid_station(station_id):
        return (
            station_id in storage.voting_stations
            and storage.voting_stations[station_id]["is_active"]
        )

    def login(self):
        ui.clear_screen()
        ui.header("E-VOTING SYSTEM", ui.THEME_LOGIN)
        print()
        ui.menu_item(1, "Login as Admin", ui.THEME_LOGIN)
        ui.menu_item(2, "Login as Voter", ui.THEME_LOGIN)
        ui.menu_item(3, "Register as Voter", ui.THEME_LOGIN)
        ui.menu_item(4, "Exit", ui.THEME_LOGIN)
        print()
        choice = ui.prompt("Enter choice: ")

        action = self._auth_menu_actions().get(choice)
        if action is not None:
            return action()
        if choice == self.REGISTER_VOTER_CHOICE:
            self.register_voter()
            return None, None
        if choice == self.EXIT_CHOICE:
            print()
            ui.info("Goodbye!")
            storage.save_data()
            raise SystemExit(0)

        return self._show_invalid_choice()

    def _login_admin(self):
        ui.clear_screen()
        ui.header("ADMIN LOGIN", ui.THEME_ADMIN)
        print()
        username = ui.prompt("Username: ")
        password = ui.masked_input("Password: ").strip()
        hashed = utils.hash_password(password)

        for admin in storage.admins.values():
            if admin["username"] == username and admin["password"] == hashed:
                if not admin["is_active"]:
                    ui.error("This account has been deactivated.")
                    utils.log_action("LOGIN_FAILED", username, "Account deactivated")
                    ui.pause()
                    return None, None
                storage.current_user = admin
                storage.current_role = "admin"
                utils.log_action("LOGIN", username, "Admin login successful")
                print()
                ui.success(f"Welcome, {admin['full_name']}!")
                ui.pause()
                return admin, "admin"

        ui.error("Invalid credentials.")
        utils.log_action("LOGIN_FAILED", username, "Invalid admin credentials")
        ui.pause()
        return None, None

    def _login_voter(self):
        ui.clear_screen()
        ui.header("VOTER LOGIN", ui.THEME_VOTER)
        print()
        voter_card = ui.prompt("Voter Card Number: ")
        password = ui.masked_input("Password: ").strip()
        hashed = utils.hash_password(password)

        for voter in storage.voters.values():
            if voter["voter_card_number"] == voter_card and voter["password"] == hashed:
                if not voter["is_active"]:
                    ui.error("This voter account has been deactivated.")
                    utils.log_action("LOGIN_FAILED", voter_card, "Voter account deactivated")
                    ui.pause()
                    return None, None
                if not voter["is_verified"]:
                    ui.warning("Your voter registration has not been verified yet.")
                    ui.info("Please contact an admin to verify your registration.")
                    utils.log_action("LOGIN_FAILED", voter_card, "Voter not verified")
                    ui.pause()
                    return None, None
                storage.current_user = voter
                storage.current_role = "voter"
                utils.log_action("LOGIN", voter_card, "Voter login successful")
                print()
                ui.success(f"Welcome, {voter['full_name']}!")
                ui.pause()
                return voter, "voter"

        ui.error("Invalid voter card number or password.")
        utils.log_action("LOGIN_FAILED", voter_card, "Invalid voter credentials")
        ui.pause()
        return None, None

    def register_voter(self):
        ui.clear_screen()
        ui.header("VOTER REGISTRATION", ui.THEME_VOTER)
        print()
        full_name = ui.prompt("Full Name: ")
        if not full_name:
            ui.error("Name cannot be empty.")
            ui.pause()
            return
        national_id = ui.prompt("National ID Number: ")
        if not national_id:
            ui.error("National ID cannot be empty.")
            ui.pause()
            return
        for voter in storage.voters.values():
            if voter["national_id"] == national_id:
                ui.error("A voter with this National ID already exists.")
                ui.pause()
                return
        dob_str = ui.prompt("Date of Birth (YYYY-MM-DD): ")
        try:
            dob = datetime.datetime.strptime(dob_str, "%Y-%m-%d")
            age = (datetime.datetime.now() - dob).days // 365
            if age < storage.MIN_VOTER_AGE:
                ui.error(f"You must be at least {storage.MIN_VOTER_AGE} years old to register.")
                ui.pause()
                return
        except ValueError:
            ui.error("Invalid date format.")
            ui.pause()
            return
        gender = ui.prompt("Gender (M/F/Other): ").upper()
        if gender not in self.VALID_GENDERS:
            ui.error("Invalid gender selection.")
            ui.pause()
            return
        address = ui.prompt("Residential Address: ")
        phone = ui.prompt("Phone Number: ")
        email = ui.prompt("Email Address: ")
        password = ui.masked_input("Create Password: ").strip()
        if len(password) < self.MIN_PASSWORD_LENGTH:
            ui.error(f"Password must be at least {self.MIN_PASSWORD_LENGTH} characters.")
            ui.pause()
            return
        confirm_password = ui.masked_input("Confirm Password: ").strip()
        if password != confirm_password:
            ui.error("Passwords do not match.")
            ui.pause()
            return
        if not storage.voting_stations:
            ui.error("No voting stations available. Contact admin.")
            ui.pause()
            return
        ui.subheader("Available Voting Stations", ui.THEME_VOTER)
        for station_id, station in storage.voting_stations.items():
            if station["is_active"]:
                print(f"    {ui.BRIGHT_BLUE}{station_id}.{ui.RESET} {station['name']} {ui.DIM}- {station['location']}{ui.RESET}")
        try:
            station_choice = int(ui.prompt("\nSelect your voting station ID: "))
            if not self._is_valid_station(station_choice):
                ui.error("Invalid station selection.")
                ui.pause()
                return
        except ValueError:
            ui.error("Invalid input.")
            ui.pause()
            return

        voter_card = utils.generate_voter_card_number()
        voter_id = storage.voter_id_counter
        storage.voters[voter_id] = {
            "id": voter_id,
            "full_name": full_name,
            "national_id": national_id,
            "date_of_birth": dob_str,
            "age": age,
            "gender": gender,
            "address": address,
            "phone": phone,
            "email": email,
            "password": utils.hash_password(password),
            "voter_card_number": voter_card,
            "station_id": station_choice,
            "is_verified": False,
            "is_active": True,
            "has_voted_in": [],
            "registered_at": str(datetime.datetime.now()),
            "role": "voter",
        }
        utils.log_action("REGISTER", full_name, f"New voter registered with card: {voter_card}")
        print()
        ui.success("Registration successful!")
        print(f"  {ui.BOLD}Your Voter Card Number: {ui.BRIGHT_YELLOW}{voter_card}{ui.RESET}")
        ui.warning("IMPORTANT: Save this number! You need it to login.")
        ui.info("Your registration is pending admin verification.")
        storage.voter_id_counter += 1
        storage.save_data()
        ui.pause()
