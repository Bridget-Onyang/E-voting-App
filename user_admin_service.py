import datetime

import storage
import ui
import utils
from service_base import UserBoundService


class VoterAdministrationService(UserBoundService):
    YES_VALUE = "yes"

    @staticmethod
    def _get_unverified_voters():
        return {
            voter_id: voter
            for voter_id, voter in storage.voters.items()
            if not voter["is_verified"]
        }

    @staticmethod
    def _show_unverified_voters(unverified):
        ui.subheader("Unverified Voters", ui.THEME_ADMIN_ACCENT)
        for voter in unverified.values():
            print(
                f"  {ui.THEME_ADMIN}{voter['id']}.{ui.RESET} {voter['full_name']} "
                f"{ui.DIM}│ NID: {voter['national_id']} │ Card: {voter['voter_card_number']}{ui.RESET}"
            )

    @staticmethod
    def _show_verify_menu():
        print()
        ui.menu_item(1, "Verify a single voter", ui.THEME_ADMIN)
        ui.menu_item(2, "Verify all pending voters", ui.THEME_ADMIN)
        return ui.prompt("\nChoice: ")

    def _verify_single_voter(self):
        try:
            voter_id = int(ui.prompt("Enter Voter ID: "))
        except ValueError:
            ui.error("Invalid input.")
            ui.pause()
            return

        if voter_id not in storage.voters:
            ui.error("Voter not found.")
            ui.pause()
            return
        if storage.voters[voter_id]["is_verified"]:
            ui.info("Already verified.")
            ui.pause()
            return

        storage.voters[voter_id]["is_verified"] = True
        utils.log_action(
            "VERIFY_VOTER",
            self.current_user["username"],
            f"Verified voter: {storage.voters[voter_id]['full_name']}",
        )
        print()
        ui.success(f"Voter '{storage.voters[voter_id]['full_name']}' verified!")
        storage.save_data()

    def _verify_all_voters(self, unverified):
        count = 0
        for voter_id in unverified:
            storage.voters[voter_id]["is_verified"] = True
            count += 1
        utils.log_action(
            "VERIFY_ALL_VOTERS",
            self.current_user["username"],
            f"Verified {count} voters",
        )
        print()
        ui.success(f"{count} voters verified!")
        storage.save_data()

    def _search_actions(self):
        return {
            "1": self._search_by_name,
            "2": self._search_by_card,
            "3": self._search_by_national_id,
            "4": self._search_by_station,
        }

    @staticmethod
    def _search_by_name():
        term = ui.prompt("Name: ").lower()
        return [voter for voter in storage.voters.values() if term in voter["full_name"].lower()]

    @staticmethod
    def _search_by_card():
        term = ui.prompt("Card Number: ")
        return [voter for voter in storage.voters.values() if term == voter["voter_card_number"]]

    @staticmethod
    def _search_by_national_id():
        term = ui.prompt("National ID: ")
        return [voter for voter in storage.voters.values() if term == voter["national_id"]]

    @staticmethod
    def _search_by_station():
        station_id = int(ui.prompt("Station ID: "))
        return [voter for voter in storage.voters.values() if voter["station_id"] == station_id]

    def view_all_voters(self):
        ui.clear_screen()
        ui.header("ALL REGISTERED VOTERS", ui.THEME_ADMIN)
        if not storage.voters:
            print()
            ui.info("No voters registered.")
            ui.pause()
            return

        print()
        ui.table_header(
            f"{'ID':<5} {'Name':<25} {'Card Number':<15} {'Stn':<6} {'Verified':<10} {'Active':<8}",
            ui.THEME_ADMIN,
        )
        ui.table_divider(70, ui.THEME_ADMIN)
        for voter in storage.voters.values():
            verified = ui.status_badge("Yes", True) if voter["is_verified"] else ui.status_badge("No", False)
            active = ui.status_badge("Yes", True) if voter["is_active"] else ui.status_badge("No", False)
            print(
                f"  {voter['id']:<5} {voter['full_name']:<25} {voter['voter_card_number']:<15} "
                f"{voter['station_id']:<6} {verified:<19} {active}"
            )
        verified_count = sum(1 for voter in storage.voters.values() if voter["is_verified"])
        unverified_count = sum(1 for voter in storage.voters.values() if not voter["is_verified"])
        print(
            f"\n  {ui.DIM}Total: {len(storage.voters)}  │  Verified: {verified_count}  │  Unverified: {unverified_count}{ui.RESET}"
        )
        ui.pause()

    def verify_voter(self):
        ui.clear_screen()
        ui.header("VERIFY VOTER", ui.THEME_ADMIN)
        unverified = self._get_unverified_voters()
        if not unverified:
            print()
            ui.info("No unverified voters.")
            ui.pause()
            return

        self._show_unverified_voters(unverified)
        choice = self._show_verify_menu()

        if choice == "1":
            self._verify_single_voter()
        elif choice == "2":
            self._verify_all_voters(unverified)
        ui.pause()

    def deactivate_voter(self):
        ui.clear_screen()
        ui.header("DEACTIVATE VOTER", ui.THEME_ADMIN)
        if not storage.voters:
            print()
            ui.info("No voters found.")
            ui.pause()
            return

        print()
        try:
            voter_id = int(ui.prompt("Enter Voter ID to deactivate: "))
        except ValueError:
            ui.error("Invalid input.")
            ui.pause()
            return

        if voter_id not in storage.voters:
            ui.error("Voter not found.")
            ui.pause()
            return
        if not storage.voters[voter_id]["is_active"]:
            ui.info("Already deactivated.")
            ui.pause()
            return

        voter_name = storage.voters[voter_id]["full_name"]
        if ui.prompt(f"Deactivate '{voter_name}'? (yes/no): ").lower() == self.YES_VALUE:
            storage.voters[voter_id]["is_active"] = False
            utils.log_action(
                "DEACTIVATE_VOTER",
                self.current_user["username"],
                f"Deactivated voter: {voter_name}",
            )
            print()
            ui.success("Voter deactivated.")
            storage.save_data()
        ui.pause()

    def search_voters(self):
        ui.clear_screen()
        ui.header("SEARCH VOTERS", ui.THEME_ADMIN)
        ui.subheader("Search by", ui.THEME_ADMIN_ACCENT)
        ui.menu_item(1, "Name", ui.THEME_ADMIN)
        ui.menu_item(2, "Voter Card Number", ui.THEME_ADMIN)
        ui.menu_item(3, "National ID", ui.THEME_ADMIN)
        ui.menu_item(4, "Station", ui.THEME_ADMIN)
        choice = ui.prompt("\nChoice: ")
        action = self._search_actions().get(choice)
        if action is None:
            ui.error("Invalid choice.")
            ui.pause()
            return

        try:
            results = action()
        except ValueError:
            ui.error("Invalid input.")
            ui.pause()
            return

        if not results:
            print()
            ui.info("No voters found.")
        else:
            print(f"\n  {ui.BOLD}Found {len(results)} voter(s):{ui.RESET}")
            for voter in results:
                verified = (
                    ui.status_badge("Verified", True)
                    if voter["is_verified"]
                    else ui.status_badge("Unverified", False)
                )
                print(
                    f"  {ui.THEME_ADMIN}ID:{ui.RESET} {voter['id']}  {ui.DIM}│{ui.RESET}  {voter['full_name']}  "
                    f"{ui.DIM}│  Card:{ui.RESET} {voter['voter_card_number']}  {ui.DIM}│{ui.RESET}  {verified}"
                )
        ui.pause()


class AdminAccountService(UserBoundService):
    MIN_PASSWORD_LENGTH = 6
    SUPER_ADMIN_ROLE = "super_admin"
    YES_VALUE = "yes"
    ROLE_MAP = {
        "1": "super_admin",
        "2": "election_officer",
        "3": "station_manager",
        "4": "auditor",
    }

    def _require_super_admin(self):
        if self.current_user["role"] == self.SUPER_ADMIN_ROLE:
            return True
        print()
        ui.error("Only super admins can perform this action.")
        ui.pause()
        return False

    def create_admin(self):
        ui.clear_screen()
        ui.header("CREATE ADMIN ACCOUNT", ui.THEME_ADMIN)
        if not self._require_super_admin():
            return

        print()
        username = ui.prompt("Username: ")
        if not username:
            ui.error("Username cannot be empty.")
            ui.pause()
            return

        for admin in storage.admins.values():
            if admin["username"] == username:
                ui.error("Username already exists.")
                ui.pause()
                return

        full_name = ui.prompt("Full Name: ")
        email = ui.prompt("Email: ")
        password = ui.masked_input("Password: ").strip()
        if len(password) < self.MIN_PASSWORD_LENGTH:
            ui.error(f"Password must be at least {self.MIN_PASSWORD_LENGTH} characters.")
            ui.pause()
            return

        ui.subheader("Available Roles", ui.THEME_ADMIN_ACCENT)
        ui.menu_item(1, f"super_admin {ui.DIM}─ Full access{ui.RESET}", ui.THEME_ADMIN)
        ui.menu_item(2, f"election_officer {ui.DIM}─ Manage polls and candidates{ui.RESET}", ui.THEME_ADMIN)
        ui.menu_item(3, f"station_manager {ui.DIM}─ Manage stations and verify voters{ui.RESET}", ui.THEME_ADMIN)
        ui.menu_item(4, f"auditor {ui.DIM}─ Read-only access{ui.RESET}", ui.THEME_ADMIN)
        role_choice = ui.prompt("\nSelect role (1-4): ")
        if role_choice not in self.ROLE_MAP:
            ui.error("Invalid role.")
            ui.pause()
            return

        role = self.ROLE_MAP[role_choice]
        admin_id = storage.admin_id_counter
        storage.admins[admin_id] = {
            "id": admin_id,
            "username": username,
            "password": utils.hash_password(password),
            "full_name": full_name,
            "email": email,
            "role": role,
            "created_at": str(datetime.datetime.now()),
            "is_active": True,
        }
        utils.log_action(
            "CREATE_ADMIN",
            self.current_user["username"],
            f"Created admin: {username} (Role: {role})",
        )
        print()
        ui.success(f"Admin '{username}' created with role: {role}")
        storage.admin_id_counter += 1
        storage.save_data()
        ui.pause()

    def view_admins(self):
        ui.clear_screen()
        ui.header("ALL ADMIN ACCOUNTS", ui.THEME_ADMIN)
        print()
        ui.table_header(
            f"{'ID':<5} {'Username':<20} {'Full Name':<25} {'Role':<20} {'Active':<8}",
            ui.THEME_ADMIN,
        )
        ui.table_divider(78, ui.THEME_ADMIN)
        for admin in storage.admins.values():
            active = ui.status_badge("Yes", True) if admin["is_active"] else ui.status_badge("No", False)
            print(
                f"  {admin['id']:<5} {admin['username']:<20} {admin['full_name']:<25} {admin['role']:<20} {active}"
            )
        print(f"\n  {ui.DIM}Total Admins: {len(storage.admins)}{ui.RESET}")
        ui.pause()

    def deactivate_admin(self):
        ui.clear_screen()
        ui.header("DEACTIVATE ADMIN", ui.THEME_ADMIN)
        if not self._require_super_admin():
            return

        print()
        for admin in storage.admins.values():
            active = ui.status_badge("Active", True) if admin["is_active"] else ui.status_badge("Inactive", False)
            print(
                f"  {ui.THEME_ADMIN}{admin['id']}.{ui.RESET} {admin['username']} "
                f"{ui.DIM}({admin['role']}){ui.RESET} {active}"
            )
        try:
            admin_id = int(ui.prompt("\nEnter Admin ID to deactivate: "))
        except ValueError:
            ui.error("Invalid input.")
            ui.pause()
            return

        if admin_id not in storage.admins:
            ui.error("Admin not found.")
            ui.pause()
            return
        if admin_id == self.current_user["id"]:
            ui.error("Cannot deactivate your own account.")
            ui.pause()
            return

        username = storage.admins[admin_id]["username"]
        if ui.prompt(f"Deactivate '{username}'? (yes/no): ").lower() == self.YES_VALUE:
            storage.admins[admin_id]["is_active"] = False
            utils.log_action(
                "DEACTIVATE_ADMIN",
                self.current_user["username"],
                f"Deactivated admin: {username}",
            )
            print()
            ui.success("Admin deactivated.")
            storage.save_data()
        ui.pause()
