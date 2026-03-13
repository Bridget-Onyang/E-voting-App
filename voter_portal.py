import datetime
import hashlib

import storage
import ui
import utils
from service_base import UserBoundService


class VoterPortal(UserBoundService):
    ABSTAIN_CHOICE = 0
    MENU_LOGOUT_CHOICE = "7"
    MANIFESTO_PREVIEW_LENGTH = 80
    PASSWORD_MIN_LENGTH = 6
    VOTE_HASH_LENGTH = 16
    RESULT_BAR_WIDTH = 50
    RESULT_BAR_SCALE = 2

    def _menu_actions(self):
        return {
            "1": self.view_open_polls,
            "2": self.cast_vote,
            "3": self.view_voting_history,
            "4": self.view_closed_poll_results,
            "5": self.view_profile,
            "6": self.change_password,
            self.MENU_LOGOUT_CHOICE: self._logout,
        }

    def _logout(self):
        utils.log_action("LOGOUT", self.current_user["voter_card_number"], "Voter logged out")
        storage.save_data()

    @staticmethod
    def _open_polls():
        return {
            poll_id: poll
            for poll_id, poll in storage.polls.items()
            if poll["status"] == "open"
        }

    def _available_polls(self, open_polls):
        voted_polls = self.current_user.get("has_voted_in", [])
        station_id = self.current_user["station_id"]
        return {
            poll_id: poll
            for poll_id, poll in open_polls.items()
            if poll_id not in voted_polls and station_id in poll["station_ids"]
        }

    @staticmethod
    def _abstain_vote(position):
        return {
            "position_id": position["position_id"],
            "position_title": position["position_title"],
            "candidate_id": None,
            "abstained": True,
        }

    @staticmethod
    def _candidate_vote(position, candidate_id):
        return {
            "position_id": position["position_id"],
            "position_title": position["position_title"],
            "candidate_id": candidate_id,
            "candidate_name": storage.candidates[candidate_id]["full_name"],
            "abstained": False,
        }

    def _record_votes(self, poll_id, my_votes, vote_timestamp, vote_hash):
        for vote in my_votes:
            storage.votes.append(
                {
                    "vote_id": vote_hash + str(vote["position_id"]),
                    "poll_id": poll_id,
                    "position_id": vote["position_id"],
                    "candidate_id": vote["candidate_id"],
                    "voter_id": self.current_user["id"],
                    "station_id": self.current_user["station_id"],
                    "timestamp": vote_timestamp,
                    "abstained": vote["abstained"],
                }
            )

    def _mark_poll_as_voted(self, poll_id):
        self.current_user["has_voted_in"].append(poll_id)
        for voter in storage.voters.values():
            if voter["id"] == self.current_user["id"]:
                voter["has_voted_in"].append(poll_id)
                break

    @staticmethod
    def _display_available_polls(available_polls):
        ui.subheader("Available Polls", ui.THEME_VOTER_ACCENT)
        for poll in available_polls.values():
            print(
                f"  {ui.THEME_VOTER}{poll['id']}.{ui.RESET} {poll['title']} "
                f"{ui.DIM}({poll['election_type']}){ui.RESET}"
            )

    def _select_poll_id(self, available_polls):
        try:
            poll_id = int(ui.prompt("\nSelect Poll ID to vote: "))
        except ValueError:
            ui.error("Invalid input.")
            ui.pause()
            return None

        if poll_id not in available_polls:
            ui.error("Invalid poll selection.")
            ui.pause()
            return None

        return poll_id

    def _collect_votes_for_poll(self, poll):
        ui.header(f"Voting: {poll['title']}", ui.THEME_VOTER)
        ui.info("Please select ONE candidate for each position.\n")
        collected_votes = []
        for position in poll["positions"]:
            vote = self._collect_vote_for_position(position)
            if vote is not None:
                collected_votes.append(vote)
        return collected_votes

    def _collect_vote_for_position(self, position):
        ui.subheader(position["position_title"], ui.THEME_VOTER_ACCENT)
        if not position["candidate_ids"]:
            ui.info("No candidates for this position.")
            return None

        for index, candidate_id in enumerate(position["candidate_ids"], 1):
            if candidate_id in storage.candidates:
                candidate = storage.candidates[candidate_id]
                print(
                    f"    {ui.THEME_VOTER}{ui.BOLD}{index}.{ui.RESET} {candidate['full_name']} "
                    f"{ui.DIM}({candidate['party']}){ui.RESET}"
                )
                print(
                    f"       {ui.DIM}Age: {candidate['age']} │ Edu: {candidate['education']} │ "
                    f"Exp: {candidate['years_experience']} yrs{ui.RESET}"
                )
                if candidate["manifesto"]:
                    print(
                        f"       {ui.ITALIC}{ui.DIM}"
                        f"{candidate['manifesto'][:self.MANIFESTO_PREVIEW_LENGTH]}...{ui.RESET}"
                    )

        print(
            f"    {ui.GRAY}{ui.BOLD}{self.ABSTAIN_CHOICE}.{ui.RESET} "
            f"{ui.GRAY}Abstain / Skip{ui.RESET}"
        )

        try:
            vote_choice = int(ui.prompt(f"\nYour choice for {position['position_title']}: "))
        except ValueError:
            ui.warning("Invalid input. Skipping.")
            vote_choice = self.ABSTAIN_CHOICE

        if vote_choice == self.ABSTAIN_CHOICE:
            return self._abstain_vote(position)
        if 1 <= vote_choice <= len(position["candidate_ids"]):
            selected_candidate_id = position["candidate_ids"][vote_choice - 1]
            return self._candidate_vote(position, selected_candidate_id)

        ui.warning("Invalid choice. Marking as abstain.")
        return self._abstain_vote(position)

    @staticmethod
    def _show_vote_summary(my_votes):
        ui.subheader("VOTE SUMMARY", ui.BRIGHT_WHITE)
        for vote in my_votes:
            if vote["abstained"]:
                print(f"  {vote['position_title']}: {ui.GRAY}ABSTAINED{ui.RESET}")
            else:
                print(
                    f"  {vote['position_title']}: "
                    f"{ui.BRIGHT_GREEN}{ui.BOLD}{vote['candidate_name']}{ui.RESET}"
                )

    @staticmethod
    def _confirm_vote_submission():
        return ui.prompt("Confirm your votes? This cannot be undone. (yes/no): ").lower() == "yes"

    def run(self):
        while True:
            ui.clear_screen()
            ui.header("VOTER DASHBOARD", ui.THEME_VOTER)
            station_name = storage.voting_stations.get(self.current_user["station_id"], {}).get("name", "Unknown")
            print(f"  {ui.THEME_VOTER}  ● {ui.RESET}{ui.BOLD}{self.current_user['full_name']}{ui.RESET}")
            print(
                f"  {ui.DIM}    Card: {self.current_user['voter_card_number']}  │  Station: {station_name}{ui.RESET}"
            )
            print()
            ui.menu_item(1, "View Open Polls", ui.THEME_VOTER)
            ui.menu_item(2, "Cast Vote", ui.THEME_VOTER)
            ui.menu_item(3, "View My Voting History", ui.THEME_VOTER)
            ui.menu_item(4, "View Results (Closed Polls)", ui.THEME_VOTER)
            ui.menu_item(5, "View My Profile", ui.THEME_VOTER)
            ui.menu_item(6, "Change Password", ui.THEME_VOTER)
            ui.menu_item(7, "Logout", ui.THEME_VOTER)
            print()
            choice = ui.prompt("Enter choice: ")

            action = self._menu_actions().get(choice)
            if action is None:
                ui.error("Invalid choice.")
                ui.pause()
                continue

            action()
            if choice == self.MENU_LOGOUT_CHOICE:
                break

    def view_open_polls(self):
        ui.clear_screen()
        ui.header("OPEN POLLS", ui.THEME_VOTER)
        open_polls = self._open_polls()
        if not open_polls:
            print()
            ui.info("No open polls at this time.")
            ui.pause()
            return

        for poll_id, poll in open_polls.items():
            already_voted = poll_id in self.current_user.get("has_voted_in", [])
            voted_status = f" {ui.GREEN}[VOTED]{ui.RESET}" if already_voted else f" {ui.YELLOW}[NOT YET VOTED]{ui.RESET}"
            print(f"\n  {ui.BOLD}{ui.THEME_VOTER}Poll #{poll['id']}: {poll['title']}{ui.RESET}{voted_status}")
            print(
                f"  {ui.DIM}Type:{ui.RESET} {poll['election_type']}  {ui.DIM}│  Period:{ui.RESET} "
                f"{poll['start_date']} to {poll['end_date']}"
            )
            for position in poll["positions"]:
                print(f"    {ui.THEME_VOTER_ACCENT}▸{ui.RESET} {ui.BOLD}{position['position_title']}{ui.RESET}")
                for candidate_id in position["candidate_ids"]:
                    if candidate_id in storage.candidates:
                        candidate = storage.candidates[candidate_id]
                        print(
                            f"      {ui.DIM}•{ui.RESET} {candidate['full_name']} {ui.DIM}({candidate['party']}) │ "
                            f"Age: {candidate['age']} │ Edu: {candidate['education']}{ui.RESET}"
                        )
        ui.pause()

    def cast_vote(self):
        ui.clear_screen()
        ui.header("CAST YOUR VOTE", ui.THEME_VOTER)
        open_polls = self._open_polls()
        if not open_polls:
            print()
            ui.info("No open polls at this time.")
            ui.pause()
            return

        available_polls = self._available_polls(open_polls)
        if not available_polls:
            print()
            ui.info("No available polls to vote in.")
            ui.pause()
            return

        self._display_available_polls(available_polls)
        poll_id = self._select_poll_id(available_polls)
        if poll_id is None:
            return

        poll = storage.polls[poll_id]
        print()
        my_votes = self._collect_votes_for_poll(poll)

        self._show_vote_summary(my_votes)
        print()
        if not self._confirm_vote_submission():
            ui.info("Vote cancelled.")
            ui.pause()
            return

        vote_timestamp = str(datetime.datetime.now())
        vote_hash = hashlib.sha256(
            f"{self.current_user['id']}{poll_id}{vote_timestamp}".encode()
        ).hexdigest()[: self.VOTE_HASH_LENGTH]
        self._record_votes(poll_id, my_votes, vote_timestamp, vote_hash)
        self._mark_poll_as_voted(poll_id)
        storage.polls[poll_id]["total_votes_cast"] += 1
        utils.log_action("CAST_VOTE", self.current_user["voter_card_number"], f"Voted in poll: {poll['title']} (Hash: {vote_hash})")
        print()
        ui.success("Your vote has been recorded successfully!")
        print(f"  {ui.DIM}Vote Reference:{ui.RESET} {ui.BRIGHT_YELLOW}{vote_hash}{ui.RESET}")
        print(f"  {ui.BRIGHT_CYAN}Thank you for participating in the democratic process!{ui.RESET}")
        storage.save_data()
        ui.pause()

    def view_voting_history(self):
        ui.clear_screen()
        ui.header("MY VOTING HISTORY", ui.THEME_VOTER)
        voted_polls = self.current_user.get("has_voted_in", [])
        if not voted_polls:
            print()
            ui.info("You have not voted in any polls yet.")
            ui.pause()
            return

        print(f"\n  {ui.DIM}You have voted in {len(voted_polls)} poll(s):{ui.RESET}\n")
        for poll_id in voted_polls:
            if poll_id in storage.polls:
                poll = storage.polls[poll_id]
                status_color = ui.GREEN if poll["status"] == "open" else ui.RED
                print(f"  {ui.BOLD}{ui.THEME_VOTER}Poll #{poll_id}: {poll['title']}{ui.RESET}")
                print(
                    f"  {ui.DIM}Type:{ui.RESET} {poll['election_type']}  {ui.DIM}│  Status:{ui.RESET} "
                    f"{status_color}{poll['status'].upper()}{ui.RESET}"
                )
                matching_votes = [
                    vote
                    for vote in storage.votes
                    if vote["poll_id"] == poll_id and vote["voter_id"] == self.current_user["id"]
                ]
                for vote in matching_votes:
                    position_title = next(
                        (
                            position["position_title"]
                            for position in poll.get("positions", [])
                            if position["position_id"] == vote["position_id"]
                        ),
                        "Unknown",
                    )
                    if vote["abstained"]:
                        print(f"    {ui.THEME_VOTER_ACCENT}▸{ui.RESET} {position_title}: {ui.GRAY}ABSTAINED{ui.RESET}")
                    else:
                        candidate_name = storage.candidates.get(vote["candidate_id"], {}).get("full_name", "Unknown")
                        print(f"    {ui.THEME_VOTER_ACCENT}▸{ui.RESET} {position_title}: {ui.BRIGHT_GREEN}{candidate_name}{ui.RESET}")
                print()
        ui.pause()

    def view_closed_poll_results(self):
        ui.clear_screen()
        ui.header("ELECTION RESULTS", ui.THEME_VOTER)
        closed_polls = {poll_id: poll for poll_id, poll in storage.polls.items() if poll["status"] == "closed"}
        if not closed_polls:
            print()
            ui.info("No closed polls with results.")
            ui.pause()
            return

        for poll_id, poll in closed_polls.items():
            print(f"\n  {ui.BOLD}{ui.THEME_VOTER}{poll['title']}{ui.RESET}")
            print(f"  {ui.DIM}Type:{ui.RESET} {poll['election_type']}  {ui.DIM}│  Votes:{ui.RESET} {poll['total_votes_cast']}")
            for position in poll["positions"]:
                ui.subheader(position["position_title"], ui.THEME_VOTER_ACCENT)
                vote_counts = {}
                abstain_count = 0
                for vote in storage.votes:
                    if vote["poll_id"] == poll_id and vote["position_id"] == position["position_id"]:
                        if vote["abstained"]:
                            abstain_count += 1
                        else:
                            vote_counts[vote["candidate_id"]] = vote_counts.get(vote["candidate_id"], 0) + 1
                total = sum(vote_counts.values()) + abstain_count
                for rank, (candidate_id, count) in enumerate(sorted(vote_counts.items(), key=lambda item: item[1], reverse=True), 1):
                    candidate = storage.candidates.get(candidate_id, {})
                    percent = (count / total * 100) if total > 0 else 0
                    filled_length = int(percent / self.RESULT_BAR_SCALE)
                    bar = (
                        f"{ui.THEME_VOTER}{'█' * filled_length}"
                        f"{ui.GRAY}{'░' * (self.RESULT_BAR_WIDTH - filled_length)}{ui.RESET}"
                    )
                    winner = f" {ui.BG_GREEN}{ui.BLACK}{ui.BOLD} WINNER {ui.RESET}" if rank <= position["max_winners"] else ""
                    print(f"    {ui.BOLD}{rank}. {candidate.get('full_name', '?')}{ui.RESET} {ui.DIM}({candidate.get('party', '?')}){ui.RESET}")
                    print(f"       {bar} {ui.BOLD}{count}{ui.RESET} ({percent:.1f}%){winner}")
                if abstain_count > 0:
                    percent = (abstain_count / total * 100) if total > 0 else 0
                    print(f"    {ui.GRAY}Abstained: {abstain_count} ({percent:.1f}%){ui.RESET}")
        ui.pause()

    def view_profile(self):
        ui.clear_screen()
        ui.header("MY PROFILE", ui.THEME_VOTER)
        voter = self.current_user
        station_name = storage.voting_stations.get(voter["station_id"], {}).get("name", "Unknown")
        print()
        for label, value in [
            ("Name", voter["full_name"]),
            ("National ID", voter["national_id"]),
            ("Voter Card", f"{ui.BRIGHT_YELLOW}{voter['voter_card_number']}{ui.RESET}"),
            ("Date of Birth", voter["date_of_birth"]),
            ("Age", voter["age"]),
            ("Gender", voter["gender"]),
            ("Address", voter["address"]),
            ("Phone", voter["phone"]),
            ("Email", voter["email"]),
            ("Station", station_name),
            ("Verified", ui.status_badge("Yes", True) if voter["is_verified"] else ui.status_badge("No", False)),
            ("Registered", voter["registered_at"]),
            ("Polls Voted", len(voter.get("has_voted_in", []))),
        ]:
            print(f"  {ui.THEME_VOTER}{label + ':':<16}{ui.RESET} {value}")
        ui.pause()

    def change_password(self):
        ui.clear_screen()
        ui.header("CHANGE PASSWORD", ui.THEME_VOTER)
        print()
        old_password = ui.masked_input("Current Password: ").strip()
        if utils.hash_password(old_password) != self.current_user["password"]:
            ui.error("Incorrect current password.")
            ui.pause()
            return
        new_password = ui.masked_input("New Password: ").strip()
        if len(new_password) < self.PASSWORD_MIN_LENGTH:
            ui.error(f"Password must be at least {self.PASSWORD_MIN_LENGTH} characters.")
            ui.pause()
            return
        confirm_password = ui.masked_input("Confirm New Password: ").strip()
        if new_password != confirm_password:
            ui.error("Passwords do not match.")
            ui.pause()
            return

        hashed_password = utils.hash_password(new_password)
        self.current_user["password"] = hashed_password
        for voter in storage.voters.values():
            if voter["id"] == self.current_user["id"]:
                voter["password"] = hashed_password
                break
        utils.log_action("CHANGE_PASSWORD", self.current_user["voter_card_number"], "Password changed")
        print()
        ui.success("Password changed successfully!")
        storage.save_data()
        ui.pause()
