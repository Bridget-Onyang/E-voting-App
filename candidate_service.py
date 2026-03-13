import datetime

import storage
import ui
import utils
from service_base import UserBoundService


class CandidateService(UserBoundService):
    VALID_GENDERS = {"M", "F", "OTHER"}
    YES_VALUE = "yes"

    @staticmethod
    def _find_candidate_by_national_id(national_id):
        return next(
            (
                candidate
                for candidate in storage.candidates.values()
                if candidate["national_id"] == national_id
            ),
            None,
        )

    @staticmethod
    def _parse_age(dob_str):
        dob = datetime.datetime.strptime(dob_str, "%Y-%m-%d")
        return (datetime.datetime.now() - dob).days // 365

    @staticmethod
    def _show_candidates_for_selection():
        for candidate in storage.candidates.values():
            print(
                f"  {ui.THEME_ADMIN}{candidate['id']}.{ui.RESET} {candidate['full_name']} "
                f"{ui.DIM}({candidate['party']}){ui.RESET}"
            )

    @staticmethod
    def _parse_experience(value):
        try:
            return int(value)
        except ValueError:
            return 0

    def create_candidate(self):
        ui.clear_screen()
        ui.header("CREATE NEW CANDIDATE", ui.THEME_ADMIN)
        print()
        full_name = ui.prompt("Full Name: ")
        if not full_name:
            ui.error("Name cannot be empty.")
            ui.pause()
            return

        national_id = ui.prompt("National ID: ")
        if not national_id:
            ui.error("National ID cannot be empty.")
            ui.pause()
            return

        if self._find_candidate_by_national_id(national_id) is not None:
            ui.error("A candidate with this National ID already exists.")
            ui.pause()
            return

        dob_str = ui.prompt("Date of Birth (YYYY-MM-DD): ")
        try:
            age = self._parse_age(dob_str)
        except ValueError:
            ui.error("Invalid date format.")
            ui.pause()
            return

        if age < storage.MIN_CANDIDATE_AGE:
            ui.error(
                f"Candidate must be at least {storage.MIN_CANDIDATE_AGE} years old. Current age: {age}"
            )
            ui.pause()
            return

        if age > storage.MAX_CANDIDATE_AGE:
            ui.error(
                f"Candidate must not be older than {storage.MAX_CANDIDATE_AGE}. Current age: {age}"
            )
            ui.pause()
            return

        gender = ui.prompt("Gender (M/F/Other): ").upper()
        if gender not in self.VALID_GENDERS:
            ui.error("Invalid gender selection.")
            ui.pause()
            return

        ui.subheader("Education Levels", ui.THEME_ADMIN_ACCENT)
        for index, level in enumerate(storage.REQUIRED_EDUCATION_LEVELS, 1):
            print(f"    {ui.THEME_ADMIN}{index}.{ui.RESET} {level}")

        try:
            education_choice = int(ui.prompt("Select education level: "))
            if education_choice < 1 or education_choice > len(storage.REQUIRED_EDUCATION_LEVELS):
                ui.error("Invalid choice.")
                ui.pause()
                return
            education = storage.REQUIRED_EDUCATION_LEVELS[education_choice - 1]
        except ValueError:
            ui.error("Invalid input.")
            ui.pause()
            return

        party = ui.prompt("Political Party/Affiliation: ")
        manifesto = ui.prompt("Brief Manifesto/Bio: ")
        address = ui.prompt("Address: ")
        phone = ui.prompt("Phone: ")
        email = ui.prompt("Email: ")
        criminal_record = ui.prompt("Has Criminal Record? (yes/no): ").lower()
        if criminal_record == self.YES_VALUE:
            ui.error("Candidates with criminal records are not eligible.")
            utils.log_action(
                "CANDIDATE_REJECTED",
                self.current_user["username"],
                f"Candidate {full_name} rejected - criminal record",
            )
            ui.pause()
            return

        years_experience = self._parse_experience(
            ui.prompt("Years of Public Service/Political Experience: ")
        )

        candidate_id = storage.candidate_id_counter
        storage.candidates[candidate_id] = {
            "id": candidate_id,
            "full_name": full_name,
            "national_id": national_id,
            "date_of_birth": dob_str,
            "age": age,
            "gender": gender,
            "education": education,
            "party": party,
            "manifesto": manifesto,
            "address": address,
            "phone": phone,
            "email": email,
            "has_criminal_record": False,
            "years_experience": years_experience,
            "is_active": True,
            "is_approved": True,
            "created_at": str(datetime.datetime.now()),
            "created_by": self.current_user["username"],
        }
        utils.log_action(
            "CREATE_CANDIDATE",
            self.current_user["username"],
            f"Created candidate: {full_name} (ID: {candidate_id})",
        )
        print()
        ui.success(f"Candidate '{full_name}' created successfully! ID: {candidate_id}")
        storage.candidate_id_counter += 1
        storage.save_data()
        ui.pause()

    def view_all_candidates(self):
        ui.clear_screen()
        ui.header("ALL CANDIDATES", ui.THEME_ADMIN)
        if not storage.candidates:
            print()
            ui.info("No candidates found.")
            ui.pause()
            return

        print()
        ui.table_header(
            f"{'ID':<5} {'Name':<25} {'Party':<20} {'Age':<5} {'Education':<20} {'Status':<10}",
            ui.THEME_ADMIN,
        )
        ui.table_divider(85, ui.THEME_ADMIN)
        for candidate in storage.candidates.values():
            status = (
                ui.status_badge("Active", True)
                if candidate["is_active"]
                else ui.status_badge("Inactive", False)
            )
            print(
                f"  {candidate['id']:<5} {candidate['full_name']:<25} {candidate['party']:<20} "
                f"{candidate['age']:<5} {candidate['education']:<20} {status}"
            )
        print(f"\n  {ui.DIM}Total Candidates: {len(storage.candidates)}{ui.RESET}")
        ui.pause()

    def update_candidate(self):
        ui.clear_screen()
        ui.header("UPDATE CANDIDATE", ui.THEME_ADMIN)
        if not storage.candidates:
            print()
            ui.info("No candidates found.")
            ui.pause()
            return

        print()
        self._show_candidates_for_selection()
        try:
            candidate_id = int(ui.prompt("\nEnter Candidate ID to update: "))
        except ValueError:
            ui.error("Invalid input.")
            ui.pause()
            return

        if candidate_id not in storage.candidates:
            ui.error("Candidate not found.")
            ui.pause()
            return

        candidate = storage.candidates[candidate_id]
        print(f"\n  {ui.BOLD}Updating: {candidate['full_name']}{ui.RESET}")
        ui.info("Press Enter to keep current value\n")
        new_name = ui.prompt(f"Full Name [{candidate['full_name']}]: ")
        if new_name:
            candidate["full_name"] = new_name
        new_party = ui.prompt(f"Party [{candidate['party']}]: ")
        if new_party:
            candidate["party"] = new_party
        new_manifesto = ui.prompt(f"Manifesto [{candidate['manifesto'][:50]}...]: ")
        if new_manifesto:
            candidate["manifesto"] = new_manifesto
        new_phone = ui.prompt(f"Phone [{candidate['phone']}]: ")
        if new_phone:
            candidate["phone"] = new_phone
        new_email = ui.prompt(f"Email [{candidate['email']}]: ")
        if new_email:
            candidate["email"] = new_email
        new_address = ui.prompt(f"Address [{candidate['address']}]: ")
        if new_address:
            candidate["address"] = new_address
        new_experience = ui.prompt(f"Years Experience [{candidate['years_experience']}]: ")
        if new_experience:
            try:
                candidate["years_experience"] = int(new_experience)
            except ValueError:
                ui.warning("Invalid number, keeping old value.")

        utils.log_action(
            "UPDATE_CANDIDATE",
            self.current_user["username"],
            f"Updated candidate: {candidate['full_name']} (ID: {candidate_id})",
        )
        print()
        ui.success(f"Candidate '{candidate['full_name']}' updated successfully!")
        storage.save_data()
        ui.pause()

    def delete_candidate(self):
        ui.clear_screen()
        ui.header("DELETE CANDIDATE", ui.THEME_ADMIN)
        if not storage.candidates:
            print()
            ui.info("No candidates found.")
            ui.pause()
            return

        print()
        for candidate in storage.candidates.values():
            status = (
                ui.status_badge("Active", True)
                if candidate["is_active"]
                else ui.status_badge("Inactive", False)
            )
            print(
                f"  {ui.THEME_ADMIN}{candidate['id']}.{ui.RESET} {candidate['full_name']} "
                f"{ui.DIM}({candidate['party']}){ui.RESET} {status}"
            )
        try:
            candidate_id = int(ui.prompt("\nEnter Candidate ID to delete: "))
        except ValueError:
            ui.error("Invalid input.")
            ui.pause()
            return

        if candidate_id not in storage.candidates:
            ui.error("Candidate not found.")
            ui.pause()
            return

        for poll in storage.polls.values():
            if poll["status"] != "open":
                continue
            for position in poll.get("positions", []):
                if candidate_id in position.get("candidate_ids", []):
                    ui.error(f"Cannot delete - candidate is in active poll: {poll['title']}")
                    ui.pause()
                    return

        candidate_name = storage.candidates[candidate_id]["full_name"]
        confirm = ui.prompt(f"Are you sure you want to delete '{candidate_name}'? (yes/no): ").lower()
        if confirm == self.YES_VALUE:
            storage.candidates[candidate_id]["is_active"] = False
            utils.log_action(
                "DELETE_CANDIDATE",
                self.current_user["username"],
                f"Deactivated candidate: {candidate_name} (ID: {candidate_id})",
            )
            print()
            ui.success(f"Candidate '{candidate_name}' has been deactivated.")
            storage.save_data()
        else:
            ui.info("Deletion cancelled.")
        ui.pause()

    def search_candidates(self):
        ui.clear_screen()
        ui.header("SEARCH CANDIDATES", ui.THEME_ADMIN)
        ui.subheader("Search by", ui.THEME_ADMIN_ACCENT)
        ui.menu_item(1, "Name", ui.THEME_ADMIN)
        ui.menu_item(2, "Party", ui.THEME_ADMIN)
        ui.menu_item(3, "Education Level", ui.THEME_ADMIN)
        ui.menu_item(4, "Age Range", ui.THEME_ADMIN)
        choice = ui.prompt("\nChoice: ")
        results = []

        if choice == "1":
            term = ui.prompt("Enter name to search: ").lower()
            results = [
                candidate
                for candidate in storage.candidates.values()
                if term in candidate["full_name"].lower()
            ]
        elif choice == "2":
            term = ui.prompt("Enter party name: ").lower()
            results = [
                candidate
                for candidate in storage.candidates.values()
                if term in candidate["party"].lower()
            ]
        elif choice == "3":
            ui.subheader("Education Levels", ui.THEME_ADMIN_ACCENT)
            for index, level in enumerate(storage.REQUIRED_EDUCATION_LEVELS, 1):
                print(f"    {ui.THEME_ADMIN}{index}.{ui.RESET} {level}")
            try:
                education_choice = int(ui.prompt("Select: "))
                education = storage.REQUIRED_EDUCATION_LEVELS[education_choice - 1]
                results = [
                    candidate
                    for candidate in storage.candidates.values()
                    if candidate["education"] == education
                ]
            except (ValueError, IndexError):
                ui.error("Invalid choice.")
                ui.pause()
                return
        elif choice == "4":
            try:
                min_age = int(ui.prompt("Min age: "))
                max_age = int(ui.prompt("Max age: "))
                results = [
                    candidate
                    for candidate in storage.candidates.values()
                    if min_age <= candidate["age"] <= max_age
                ]
            except ValueError:
                ui.error("Invalid input.")
                ui.pause()
                return
        else:
            ui.error("Invalid choice.")
            ui.pause()
            return

        if not results:
            print()
            ui.info("No candidates found matching your criteria.")
        else:
            print(f"\n  {ui.BOLD}Found {len(results)} candidate(s):{ui.RESET}")
            ui.table_header(
                f"{'ID':<5} {'Name':<25} {'Party':<20} {'Age':<5} {'Education':<20}",
                ui.THEME_ADMIN,
            )
            ui.table_divider(75, ui.THEME_ADMIN)
            for candidate in results:
                print(
                    f"  {candidate['id']:<5} {candidate['full_name']:<25} {candidate['party']:<20} "
                    f"{candidate['age']:<5} {candidate['education']:<20}"
                )
        ui.pause()
