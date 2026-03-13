import datetime

import storage
import ui
import utils
from service_base import UserBoundService


class PollService(UserBoundService):
    STATUS_DRAFT = "draft"
    STATUS_OPEN = "open"
    STATUS_CLOSED = "closed"
    YES_VALUE = "yes"

    @staticmethod
    def _status_color(status):
        if status == PollService.STATUS_OPEN:
            return ui.GREEN
        if status == PollService.STATUS_DRAFT:
            return ui.YELLOW
        return ui.RED

    @staticmethod
    def _parse_csv_ids(raw_value):
        return [int(value.strip()) for value in raw_value.split(",") if value.strip()]

    @staticmethod
    def _eligible_candidates_for_position(position):
        active_candidates = {
            candidate_id: candidate
            for candidate_id, candidate in storage.candidates.items()
            if candidate["is_active"] and candidate["is_approved"]
        }
        position_data = storage.positions.get(position["position_id"], {})
        min_age = position_data.get("min_candidate_age", storage.MIN_CANDIDATE_AGE)
        return {
            candidate_id: candidate
            for candidate_id, candidate in active_candidates.items()
            if candidate["age"] >= min_age
        }

    @staticmethod
    def _show_available_candidates(eligible_candidates, assigned_ids):
        ui.subheader("Available Candidates", ui.THEME_ADMIN)
        for candidate in eligible_candidates.values():
            marker = f" {ui.GREEN}[ASSIGNED]{ui.RESET}" if candidate["id"] in assigned_ids else ""
            print(
                f"    {ui.THEME_ADMIN}{candidate['id']}.{ui.RESET} {candidate['full_name']} "
                f"{ui.DIM}({candidate['party']}) - Age: {candidate['age']}, Edu: {candidate['education']}{ui.RESET}{marker}"
            )

    def _collect_assigned_candidate_ids(self, eligible_candidates):
        try:
            requested_ids = self._parse_csv_ids(ui.prompt("Enter Candidate IDs (comma-separated): "))
        except ValueError:
            ui.error("Invalid input. Skipping this position.")
            return None

        valid_ids = []
        for candidate_id in requested_ids:
            if candidate_id in eligible_candidates:
                valid_ids.append(candidate_id)
            else:
                ui.warning(f"Candidate {candidate_id} not eligible. Skipping.")
        return valid_ids

    def _assign_candidates_for_position(self, position):
        ui.subheader(f"Position: {position['position_title']}", ui.THEME_ADMIN_ACCENT)
        current_candidates = [
            f"{candidate_id}: {storage.candidates[candidate_id]['full_name']}"
            for candidate_id in position["candidate_ids"]
            if candidate_id in storage.candidates
        ]
        if current_candidates:
            print(f"  {ui.DIM}Current:{ui.RESET} {', '.join(current_candidates)}")
        else:
            ui.info("No candidates assigned yet.")

        eligible_candidates = self._eligible_candidates_for_position(position)
        if not eligible_candidates:
            ui.info("No eligible candidates found.")
            return

        self._show_available_candidates(eligible_candidates, position["candidate_ids"])
        should_modify = ui.prompt(
            f"\nModify candidates for {position['position_title']}? (yes/no): "
        ).lower() == self.YES_VALUE
        if not should_modify:
            return

        new_ids = self._collect_assigned_candidate_ids(eligible_candidates)
        if new_ids is None:
            return
        position["candidate_ids"] = new_ids
        ui.success(f"{len(new_ids)} candidate(s) assigned.")

    def create_poll(self):
        ui.clear_screen()
        ui.header("CREATE POLL / ELECTION", ui.THEME_ADMIN)
        print()
        title = ui.prompt("Poll/Election Title: ")
        if not title:
            ui.error("Title cannot be empty.")
            ui.pause()
            return

        description = ui.prompt("Description: ")
        election_type = ui.prompt("Election Type (General/Primary/By-election/Referendum): ")
        start_date = ui.prompt("Start Date (YYYY-MM-DD): ")
        end_date = ui.prompt("End Date (YYYY-MM-DD): ")
        try:
            start = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.datetime.strptime(end_date, "%Y-%m-%d")
            if end <= start:
                ui.error("End date must be after start date.")
                ui.pause()
                return
        except ValueError:
            ui.error("Invalid date format.")
            ui.pause()
            return

        if not storage.positions:
            ui.error("No positions available. Create positions first.")
            ui.pause()
            return

        ui.subheader("Available Positions", ui.THEME_ADMIN_ACCENT)
        active_positions = {
            position_id: position
            for position_id, position in storage.positions.items()
            if position["is_active"]
        }
        if not active_positions:
            ui.error("No active positions.")
            ui.pause()
            return

        for position in active_positions.values():
            print(
                f"    {ui.THEME_ADMIN}{position['id']}.{ui.RESET} {position['title']} "
                f"{ui.DIM}({position['level']}) - {position['max_winners']} seat(s){ui.RESET}"
            )
        try:
            selected_position_ids = [
                int(value.strip())
                for value in ui.prompt("\nEnter Position IDs (comma-separated): ").split(",")
            ]
        except ValueError:
            ui.error("Invalid input.")
            ui.pause()
            return

        poll_positions = []
        for position_id in selected_position_ids:
            if position_id not in active_positions:
                ui.warning(f"Position ID {position_id} not found or inactive. Skipping.")
                continue
            position = storage.positions[position_id]
            poll_positions.append(
                {
                    "position_id": position_id,
                    "position_title": position["title"],
                    "candidate_ids": [],
                    "max_winners": position["max_winners"],
                }
            )
        if not poll_positions:
            ui.error("No valid positions selected.")
            ui.pause()
            return

        if not storage.voting_stations:
            ui.error("No voting stations. Create stations first.")
            ui.pause()
            return

        ui.subheader("Available Voting Stations", ui.THEME_ADMIN_ACCENT)
        active_stations = {
            station_id: station
            for station_id, station in storage.voting_stations.items()
            if station["is_active"]
        }
        if not active_stations:
            ui.error("No active voting stations.")
            ui.pause()
            return

        for station in active_stations.values():
            print(
                f"    {ui.THEME_ADMIN}{station['id']}.{ui.RESET} {station['name']} "
                f"{ui.DIM}({station['location']}){ui.RESET}"
            )

        if ui.prompt("\nUse all active stations? (yes/no): ").lower() == self.YES_VALUE:
            selected_station_ids = list(active_stations.keys())
        else:
            try:
                input_station_ids = self._parse_csv_ids(
                    ui.prompt("Enter Station IDs (comma-separated): ")
                )
            except ValueError:
                ui.error("Invalid input.")
                ui.pause()
                return

            selected_station_ids = []
            for station_id in input_station_ids:
                if station_id in active_stations:
                    selected_station_ids.append(station_id)
                else:
                    ui.warning(f"Station ID {station_id} not found or inactive. Skipping.")

            if not selected_station_ids:
                ui.error("No valid active stations selected.")
                ui.pause()
                return

        poll_id = storage.poll_id_counter
        storage.polls[poll_id] = {
            "id": poll_id,
            "title": title,
            "description": description,
            "election_type": election_type,
            "start_date": start_date,
            "end_date": end_date,
            "positions": poll_positions,
            "station_ids": selected_station_ids,
            "status": self.STATUS_DRAFT,
            "total_votes_cast": 0,
            "created_at": str(datetime.datetime.now()),
            "created_by": self.current_user["username"],
        }
        utils.log_action(
            "CREATE_POLL",
            self.current_user["username"],
            f"Created poll: {title} (ID: {poll_id})",
        )
        print()
        ui.success(f"Poll '{title}' created! ID: {poll_id}")
        ui.warning("Status: DRAFT - Assign candidates and then open the poll.")
        storage.poll_id_counter += 1
        storage.save_data()
        ui.pause()

    def view_all_polls(self):
        ui.clear_screen()
        ui.header("ALL POLLS / ELECTIONS", ui.THEME_ADMIN)
        if not storage.polls:
            print()
            ui.info("No polls found.")
            ui.pause()
            return

        for poll in storage.polls.values():
            status_color = self._status_color(poll["status"])
            print(f"\n  {ui.BOLD}{ui.THEME_ADMIN}Poll #{poll['id']}: {poll['title']}{ui.RESET}")
            print(
                f"  {ui.DIM}Type:{ui.RESET} {poll['election_type']}  {ui.DIM}│  Status:{ui.RESET} "
                f"{status_color}{ui.BOLD}{poll['status'].upper()}{ui.RESET}"
            )
            print(
                f"  {ui.DIM}Period:{ui.RESET} {poll['start_date']} to {poll['end_date']}  "
                f"{ui.DIM}│  Votes:{ui.RESET} {poll['total_votes_cast']}"
            )
            for position in poll["positions"]:
                candidate_names = [
                    storage.candidates[candidate_id]["full_name"]
                    for candidate_id in position["candidate_ids"]
                    if candidate_id in storage.candidates
                ]
                candidate_display = ", ".join(candidate_names) if candidate_names else f"{ui.DIM}None assigned{ui.RESET}"
                print(f"    {ui.THEME_ADMIN_ACCENT}▸{ui.RESET} {position['position_title']}: {candidate_display}")
        print(f"\n  {ui.DIM}Total Polls: {len(storage.polls)}{ui.RESET}")
        ui.pause()

    def update_poll(self):
        ui.clear_screen()
        ui.header("UPDATE POLL", ui.THEME_ADMIN)
        if not storage.polls:
            print()
            ui.info("No polls found.")
            ui.pause()
            return

        print()
        for poll in storage.polls.values():
            status_color = self._status_color(poll["status"])
            print(f"  {ui.THEME_ADMIN}{poll['id']}.{ui.RESET} {poll['title']} {status_color}({poll['status']}){ui.RESET}")

        try:
            poll_id = int(ui.prompt("\nEnter Poll ID to update: "))
        except ValueError:
            ui.error("Invalid input.")
            ui.pause()
            return

        if poll_id not in storage.polls:
            ui.error("Poll not found.")
            ui.pause()
            return

        poll = storage.polls[poll_id]
        if poll["status"] == self.STATUS_OPEN:
            ui.error("Cannot update an open poll. Close it first.")
            ui.pause()
            return
        if poll["status"] == self.STATUS_CLOSED and poll["total_votes_cast"] > 0:
            ui.error("Cannot update a poll with votes.")
            ui.pause()
            return

        original_start_date = poll["start_date"]
        original_end_date = poll["end_date"]

        print(f"\n  {ui.BOLD}Updating: {poll['title']}{ui.RESET}")
        ui.info("Press Enter to keep current value\n")
        new_title = ui.prompt(f"Title [{poll['title']}]: ")
        if new_title:
            poll["title"] = new_title
        new_description = ui.prompt(f"Description [{poll['description'][:50]}]: ")
        if new_description:
            poll["description"] = new_description
        new_type = ui.prompt(f"Election Type [{poll['election_type']}]: ")
        if new_type:
            poll["election_type"] = new_type
        new_start = ui.prompt(f"Start Date [{poll['start_date']}]: ")
        if new_start:
            try:
                datetime.datetime.strptime(new_start, "%Y-%m-%d")
                poll["start_date"] = new_start
            except ValueError:
                ui.warning("Invalid date, keeping old value.")
        new_end = ui.prompt(f"End Date [{poll['end_date']}]: ")
        if new_end:
            try:
                datetime.datetime.strptime(new_end, "%Y-%m-%d")
                poll["end_date"] = new_end
            except ValueError:
                ui.warning("Invalid date, keeping old value.")

        try:
            updated_start = datetime.datetime.strptime(poll["start_date"], "%Y-%m-%d")
            updated_end = datetime.datetime.strptime(poll["end_date"], "%Y-%m-%d")
            if updated_end <= updated_start:
                ui.warning("Invalid date range. Reverting to original dates.")
                poll["start_date"] = original_start_date
                poll["end_date"] = original_end_date
        except ValueError:
            ui.warning("Invalid date values detected. Keeping original dates.")

        utils.log_action(
            "UPDATE_POLL",
            self.current_user["username"],
            f"Updated poll: {poll['title']}",
        )
        print()
        ui.success("Poll updated!")
        storage.save_data()
        ui.pause()

    def delete_poll(self):
        ui.clear_screen()
        ui.header("DELETE POLL", ui.THEME_ADMIN)
        if not storage.polls:
            print()
            ui.info("No polls found.")
            ui.pause()
            return

        print()
        for poll in storage.polls.values():
            print(f"  {ui.THEME_ADMIN}{poll['id']}.{ui.RESET} {poll['title']} {ui.DIM}({poll['status']}){ui.RESET}")
        try:
            poll_id = int(ui.prompt("\nEnter Poll ID to delete: "))
        except ValueError:
            ui.error("Invalid input.")
            ui.pause()
            return

        if poll_id not in storage.polls:
            ui.error("Poll not found.")
            ui.pause()
            return
        if storage.polls[poll_id]["status"] == self.STATUS_OPEN:
            ui.error("Cannot delete an open poll. Close it first.")
            ui.pause()
            return
        if storage.polls[poll_id]["total_votes_cast"] > 0:
            ui.warning(f"This poll has {storage.polls[poll_id]['total_votes_cast']} votes recorded.")

        if ui.prompt(f"Confirm deletion of '{storage.polls[poll_id]['title']}'? (yes/no): ").lower() == self.YES_VALUE:
            deleted_title = storage.polls[poll_id]["title"]
            del storage.polls[poll_id]
            storage.votes[:] = [vote for vote in storage.votes if vote["poll_id"] != poll_id]
            utils.log_action(
                "DELETE_POLL",
                self.current_user["username"],
                f"Deleted poll: {deleted_title}",
            )
            print()
            ui.success(f"Poll '{deleted_title}' deleted.")
            storage.save_data()
        ui.pause()

    def open_close_poll(self):
        ui.clear_screen()
        ui.header("OPEN / CLOSE POLL", ui.THEME_ADMIN)
        if not storage.polls:
            print()
            ui.info("No polls found.")
            ui.pause()
            return

        print()
        for poll in storage.polls.values():
            status_color = self._status_color(poll["status"])
            print(
                f"  {ui.THEME_ADMIN}{poll['id']}.{ui.RESET} {poll['title']}  "
                f"{status_color}{ui.BOLD}{poll['status'].upper()}{ui.RESET}"
            )
        try:
            poll_id = int(ui.prompt("\nEnter Poll ID: "))
        except ValueError:
            ui.error("Invalid input.")
            ui.pause()
            return

        if poll_id not in storage.polls:
            ui.error("Poll not found.")
            ui.pause()
            return

        poll = storage.polls[poll_id]
        if poll["status"] == self.STATUS_DRAFT:
            if not any(position["candidate_ids"] for position in poll["positions"]):
                ui.error("Cannot open - no candidates assigned.")
                ui.pause()
                return
            if ui.prompt(f"Open poll '{poll['title']}'? Voting will begin. (yes/no): ").lower() == self.YES_VALUE:
                poll["status"] = self.STATUS_OPEN
                utils.log_action("OPEN_POLL", self.current_user["username"], f"Opened poll: {poll['title']}")
                print()
                ui.success(f"Poll '{poll['title']}' is now OPEN for voting!")
                storage.save_data()
        elif poll["status"] == self.STATUS_OPEN:
            if ui.prompt(f"Close poll '{poll['title']}'? No more votes accepted. (yes/no): ").lower() == self.YES_VALUE:
                poll["status"] = self.STATUS_CLOSED
                utils.log_action("CLOSE_POLL", self.current_user["username"], f"Closed poll: {poll['title']}")
                print()
                ui.success(f"Poll '{poll['title']}' is now CLOSED.")
                storage.save_data()
        elif poll["status"] == self.STATUS_CLOSED:
            ui.info("This poll is already closed.")
            if ui.prompt("Reopen it? (yes/no): ").lower() == self.YES_VALUE:
                poll["status"] = self.STATUS_OPEN
                utils.log_action("REOPEN_POLL", self.current_user["username"], f"Reopened poll: {poll['title']}")
                print()
                ui.success("Poll reopened!")
                storage.save_data()
        ui.pause()

    def assign_candidates_to_poll(self):
        ui.clear_screen()
        ui.header("ASSIGN CANDIDATES TO POLL", ui.THEME_ADMIN)
        if not storage.polls:
            print()
            ui.info("No polls found.")
            ui.pause()
            return
        if not storage.candidates:
            print()
            ui.info("No candidates found.")
            ui.pause()
            return

        print()
        for poll in storage.polls.values():
            print(f"  {ui.THEME_ADMIN}{poll['id']}.{ui.RESET} {poll['title']} {ui.DIM}({poll['status']}){ui.RESET}")
        try:
            poll_id = int(ui.prompt("\nEnter Poll ID: "))
        except ValueError:
            ui.error("Invalid input.")
            ui.pause()
            return

        if poll_id not in storage.polls:
            ui.error("Poll not found.")
            ui.pause()
            return

        poll = storage.polls[poll_id]
        if poll["status"] == self.STATUS_OPEN:
            ui.error("Cannot modify candidates of an open poll.")
            ui.pause()
            return

        for position in poll["positions"]:
            self._assign_candidates_for_position(position)

        utils.log_action(
            "ASSIGN_CANDIDATES",
            self.current_user["username"],
            f"Updated candidates for poll: {poll['title']}",
        )
        storage.save_data()
        ui.pause()
