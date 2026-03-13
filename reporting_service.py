import storage
import ui


class ReportingService:
    RESULT_BAR_WIDTH = 50
    RESULT_BAR_SCALE = 2
    TURNOUT_HIGH_THRESHOLD = 50
    TURNOUT_MEDIUM_THRESHOLD = 25
    LAST_LOG_ENTRIES_COUNT = 20

    @staticmethod
    def _status_color(status):
        if status == "open":
            return ui.GREEN
        if status == "draft":
            return ui.YELLOW
        return ui.RED

    @staticmethod
    def _action_color(action):
        if "CREATE" in action or action == "LOGIN":
            return ui.GREEN
        if "DELETE" in action or "DEACTIVATE" in action:
            return ui.RED
        if "UPDATE" in action:
            return ui.YELLOW
        return ui.RESET

    def _turnout_color(self, turnout):
        if turnout > self.TURNOUT_HIGH_THRESHOLD:
            return ui.GREEN
        if turnout > self.TURNOUT_MEDIUM_THRESHOLD:
            return ui.YELLOW
        return ui.RED

    def _result_bar(self, percent):
        bar_length = int(percent / self.RESULT_BAR_SCALE)
        return (
            f"{ui.THEME_ADMIN}{'█' * bar_length}"
            f"{ui.GRAY}{'░' * (self.RESULT_BAR_WIDTH - bar_length)}{ui.RESET}"
        )

    @staticmethod
    def _age_group_counts():
        age_groups = {"18-25": 0, "26-35": 0, "36-45": 0, "46-55": 0, "56-65": 0, "65+": 0}
        for voter in storage.voters.values():
            age = voter.get("age", 0)
            if age <= 25:
                age_groups["18-25"] += 1
            elif age <= 35:
                age_groups["26-35"] += 1
            elif age <= 45:
                age_groups["36-45"] += 1
            elif age <= 55:
                age_groups["46-55"] += 1
            elif age <= 65:
                age_groups["56-65"] += 1
            else:
                age_groups["65+"] += 1
        return age_groups

    @staticmethod
    def _gender_counts():
        counts = {}
        for voter in storage.voters.values():
            gender = voter.get("gender", "?")
            counts[gender] = counts.get(gender, 0) + 1
        return counts

    def _render_system_overview(self):
        ui.subheader("SYSTEM OVERVIEW", ui.THEME_ADMIN_ACCENT)
        total_candidates = len(storage.candidates)
        active_candidates = sum(1 for candidate in storage.candidates.values() if candidate["is_active"])
        total_voters = len(storage.voters)
        verified_voters = sum(1 for voter in storage.voters.values() if voter["is_verified"])
        active_voters = sum(1 for voter in storage.voters.values() if voter["is_active"])
        total_stations = len(storage.voting_stations)
        active_stations = sum(1 for station in storage.voting_stations.values() if station["is_active"])
        total_polls = len(storage.polls)
        open_polls = sum(1 for poll in storage.polls.values() if poll["status"] == "open")
        closed_polls = sum(1 for poll in storage.polls.values() if poll["status"] == "closed")
        draft_polls = sum(1 for poll in storage.polls.values() if poll["status"] == "draft")

        print(f"  {ui.THEME_ADMIN}Candidates:{ui.RESET}  {total_candidates} {ui.DIM}(Active: {active_candidates}){ui.RESET}")
        print(f"  {ui.THEME_ADMIN}Voters:{ui.RESET}      {total_voters} {ui.DIM}(Verified: {verified_voters}, Active: {active_voters}){ui.RESET}")
        print(f"  {ui.THEME_ADMIN}Stations:{ui.RESET}    {total_stations} {ui.DIM}(Active: {active_stations}){ui.RESET}")
        print(
            f"  {ui.THEME_ADMIN}Polls:{ui.RESET}       {total_polls} {ui.DIM}("
            f"{ui.GREEN}Open: {open_polls}{ui.RESET}{ui.DIM}, {ui.RED}Closed: {closed_polls}{ui.RESET}{ui.DIM}, "
            f"{ui.YELLOW}Draft: {draft_polls}{ui.RESET}{ui.DIM}){ui.RESET}"
        )
        print(f"  {ui.THEME_ADMIN}Total Votes:{ui.RESET} {len(storage.votes)}")

    def _render_voter_demographics(self):
        ui.subheader("VOTER DEMOGRAPHICS", ui.THEME_ADMIN_ACCENT)
        total_voters = len(storage.voters)
        gender_counts = self._gender_counts()
        age_groups = self._age_group_counts()

        for gender, count in gender_counts.items():
            percent = (count / total_voters * 100) if total_voters > 0 else 0
            print(f"    {gender}: {count} ({percent:.1f}%)")

        print(f"  {ui.BOLD}Age Distribution:{ui.RESET}")
        for group, count in age_groups.items():
            percent = (count / total_voters * 100) if total_voters > 0 else 0
            print(
                f"    {group:>5}: {count:>3} ({percent:>5.1f}%) "
                f"{ui.THEME_ADMIN}{'█' * int(percent / 2)}{ui.RESET}"
            )

    @staticmethod
    def _render_candidate_party_distribution():
        ui.subheader("CANDIDATE PARTY DISTRIBUTION", ui.THEME_ADMIN_ACCENT)
        party_counts = {}
        for candidate in storage.candidates.values():
            if candidate["is_active"]:
                party_counts[candidate["party"]] = party_counts.get(candidate["party"], 0) + 1
        for party, count in sorted(party_counts.items(), key=lambda item: item[1], reverse=True):
            print(f"    {party}: {ui.BOLD}{count}{ui.RESET} candidate(s)")

    @staticmethod
    def _render_candidate_education_levels():
        ui.subheader("CANDIDATE EDUCATION LEVELS", ui.THEME_ADMIN_ACCENT)
        education_counts = {}
        for candidate in storage.candidates.values():
            if candidate["is_active"]:
                education_counts[candidate["education"]] = education_counts.get(candidate["education"], 0) + 1
        for education, count in education_counts.items():
            print(f"    {education}: {ui.BOLD}{count}{ui.RESET}")

    @staticmethod
    def _render_station_load():
        ui.subheader("STATION LOAD", ui.THEME_ADMIN_ACCENT)
        for station in storage.voting_stations.values():
            voter_count = sum(1 for voter in storage.voters.values() if voter["station_id"] == station["id"])
            load_percent = (voter_count / station["capacity"] * 100) if station["capacity"] > 0 else 0
            load_color = ui.RED if load_percent > 100 else (ui.YELLOW if load_percent > 75 else ui.GREEN)
            status = f"{ui.RED}{ui.BOLD}OVERLOADED{ui.RESET}" if load_percent > 100 else f"{ui.GREEN}OK{ui.RESET}"
            print(
                f"    {station['name']}: {voter_count}/{station['capacity']} "
                f"{load_color}({load_percent:.0f}%){ui.RESET} {status}"
            )

    def view_poll_results(self):
        ui.clear_screen()
        ui.header("POLL RESULTS", ui.THEME_ADMIN)
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
        print()
        ui.header(f"RESULTS: {poll['title']}", ui.THEME_ADMIN)
        status_color = self._status_color(poll["status"])
        print(
            f"  {ui.DIM}Status:{ui.RESET} {status_color}{ui.BOLD}{poll['status'].upper()}{ui.RESET}  "
            f"{ui.DIM}│  Votes:{ui.RESET} {ui.BOLD}{poll['total_votes_cast']}{ui.RESET}"
        )
        total_eligible = sum(
            1
            for voter in storage.voters.values()
            if voter["is_verified"] and voter["is_active"] and voter["station_id"] in poll["station_ids"]
        )
        turnout = (poll["total_votes_cast"] / total_eligible * 100) if total_eligible > 0 else 0
        turnout_color = self._turnout_color(turnout)
        print(
            f"  {ui.DIM}Eligible:{ui.RESET} {total_eligible}  {ui.DIM}│  Turnout:{ui.RESET} "
            f"{turnout_color}{ui.BOLD}{turnout:.1f}%{ui.RESET}"
        )
        for position in poll["positions"]:
            ui.subheader(f"{position['position_title']} (Seats: {position['max_winners']})", ui.THEME_ADMIN_ACCENT)
            vote_counts = {}
            abstain_count = 0
            total_position_votes = 0
            for vote in storage.votes:
                if vote["poll_id"] == poll_id and vote["position_id"] == position["position_id"]:
                    total_position_votes += 1
                    if vote["abstained"]:
                        abstain_count += 1
                    else:
                        vote_counts[vote["candidate_id"]] = vote_counts.get(vote["candidate_id"], 0) + 1
            for rank, (candidate_id, count) in enumerate(
                sorted(vote_counts.items(), key=lambda item: item[1], reverse=True),
                1,
            ):
                candidate = storage.candidates.get(candidate_id, {})
                percent = (count / total_position_votes * 100) if total_position_votes > 0 else 0
                bar = self._result_bar(percent)
                winner = f" {ui.BG_GREEN}{ui.BLACK}{ui.BOLD} ★ WINNER {ui.RESET}" if rank <= position["max_winners"] else ""
                print(f"    {ui.BOLD}{rank}. {candidate.get('full_name', '?')}{ui.RESET} {ui.DIM}({candidate.get('party', '?')}){ui.RESET}")
                print(f"       {bar} {ui.BOLD}{count}{ui.RESET} ({percent:.1f}%){winner}")
            if abstain_count > 0:
                percent = (abstain_count / total_position_votes * 100) if total_position_votes > 0 else 0
                print(f"    {ui.GRAY}Abstained: {abstain_count} ({percent:.1f}%){ui.RESET}")
            if not vote_counts:
                ui.info("    No votes recorded for this position.")
        ui.pause()

    def view_detailed_statistics(self):
        ui.clear_screen()
        ui.header("DETAILED STATISTICS", ui.THEME_ADMIN)
        self._render_system_overview()
        self._render_voter_demographics()
        self._render_station_load()
        self._render_candidate_party_distribution()
        self._render_candidate_education_levels()
        ui.pause()

    def station_wise_results(self):
        ui.clear_screen()
        ui.header("STATION-WISE RESULTS", ui.THEME_ADMIN)
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
        print()
        ui.header(f"STATION RESULTS: {poll['title']}", ui.THEME_ADMIN)
        for station_id in poll["station_ids"]:
            if station_id not in storage.voting_stations:
                continue
            station = storage.voting_stations[station_id]
            ui.subheader(f"{station['name']}  ({station['location']})", ui.BRIGHT_WHITE)
            station_votes = [vote for vote in storage.votes if vote["poll_id"] == poll_id and vote["station_id"] == station_id]
            voted_count = len(set(vote["voter_id"] for vote in station_votes))
            registered_active = sum(
                1
                for voter in storage.voters.values()
                if voter["station_id"] == station_id and voter["is_verified"] and voter["is_active"]
            )
            turnout = (voted_count / registered_active * 100) if registered_active > 0 else 0
            turnout_color = self._turnout_color(turnout)
            print(
                f"  {ui.DIM}Registered:{ui.RESET} {registered_active}  {ui.DIM}│  Voted:{ui.RESET} {voted_count}  "
                f"{ui.DIM}│  Turnout:{ui.RESET} {turnout_color}{ui.BOLD}{turnout:.1f}%{ui.RESET}"
            )
            for position in poll["positions"]:
                print(f"    {ui.THEME_ADMIN_ACCENT}▸ {position['position_title']}:{ui.RESET}")
                position_votes = [
                    vote for vote in station_votes if vote["position_id"] == position["position_id"]
                ]
                vote_counts = {}
                abstain_count = 0
                for vote in position_votes:
                    if vote["abstained"]:
                        abstain_count += 1
                    else:
                        vote_counts[vote["candidate_id"]] = vote_counts.get(vote["candidate_id"], 0) + 1
                total = sum(vote_counts.values()) + abstain_count
                for candidate_id, count in sorted(vote_counts.items(), key=lambda item: item[1], reverse=True):
                    candidate = storage.candidates.get(candidate_id, {})
                    percent = (count / total * 100) if total > 0 else 0
                    print(
                        f"      {candidate.get('full_name', '?')} {ui.DIM}({candidate.get('party', '?')}){ui.RESET}: "
                        f"{ui.BOLD}{count}{ui.RESET} ({percent:.1f}%)"
                    )
                if abstain_count > 0:
                    percent = (abstain_count / total * 100) if total > 0 else 0
                    print(f"      {ui.GRAY}Abstained: {abstain_count} ({percent:.1f}%){ui.RESET}")
        ui.pause()

    def view_audit_log(self):
        ui.clear_screen()
        ui.header("AUDIT LOG", ui.THEME_ADMIN)
        if not storage.audit_log:
            print()
            ui.info("No audit records.")
            ui.pause()
            return

        print(f"\n  {ui.DIM}Total Records: {len(storage.audit_log)}{ui.RESET}")
        ui.subheader("Filter", ui.THEME_ADMIN_ACCENT)
        ui.menu_item(1, "Last 20 entries", ui.THEME_ADMIN)
        ui.menu_item(2, "All entries", ui.THEME_ADMIN)
        ui.menu_item(3, "Filter by action type", ui.THEME_ADMIN)
        ui.menu_item(4, "Filter by user", ui.THEME_ADMIN)
        choice = ui.prompt("\nChoice: ")
        entries = storage.audit_log
        if choice == "1":
            entries = storage.audit_log[-self.LAST_LOG_ENTRIES_COUNT:]
        elif choice == "3":
            action_types = list(set(entry["action"] for entry in storage.audit_log))
            for index, action_type in enumerate(action_types, 1):
                print(f"    {ui.THEME_ADMIN}{index}.{ui.RESET} {action_type}")
            try:
                action_choice = int(ui.prompt("Select action type: "))
                entries = [
                    entry for entry in storage.audit_log if entry["action"] == action_types[action_choice - 1]
                ]
            except (ValueError, IndexError):
                ui.error("Invalid choice.")
                ui.pause()
                return
        elif choice == "4":
            user_filter = ui.prompt("Enter username/card number: ")
            entries = [
                entry for entry in storage.audit_log if user_filter.lower() in entry["user"].lower()
            ]

        print()
        ui.table_header(f"{'Timestamp':<22} {'Action':<25} {'User':<20} {'Details'}", ui.THEME_ADMIN)
        ui.table_divider(100, ui.THEME_ADMIN)
        for entry in entries:
            action_color = self._action_color(entry["action"])
            print(
                f"  {ui.DIM}{entry['timestamp'][:19]}{ui.RESET}  {action_color}{entry['action']:<25}{ui.RESET} "
                f"{entry['user']:<20} {ui.DIM}{entry['details'][:50]}{ui.RESET}"
            )
        ui.pause()
