from candidate_service import CandidateService
from poll_service import PollService
from position_service import PositionService
from reporting_service import ReportingService
from station_service import StationService
from user_admin_service import AdminAccountService, VoterAdministrationService
import storage
import ui
import utils


class AdminDashboard:
    SAVE_DATA_CHOICE = "31"
    LOGOUT_CHOICE = "32"

    def __init__(self):
        self.current_user = None
        self.candidate_manager = CandidateService()
        self.station_manager = StationService()
        self.position_manager = PositionService()
        self.poll_manager = PollService()
        self.voter_manager = VoterAdministrationService()
        self.admin_account_manager = AdminAccountService()
        self.reporting_service = ReportingService()
        self._user_bound_services = [
            self.candidate_manager,
            self.station_manager,
            self.position_manager,
            self.poll_manager,
            self.voter_manager,
            self.admin_account_manager,
        ]
        self._actions = self._build_menu_actions()

    def set_current_user(self, user):
        self.current_user = user
        for service in self._user_bound_services:
            service.set_current_user(user)

    def _save_data(self):
        storage.save_data()
        ui.pause()

    def _logout(self):
        utils.log_action("LOGOUT", self.current_user["username"], "Admin logged out")
        storage.save_data()

    def _build_menu_actions(self):
        return {
            "1": self.candidate_manager.create_candidate,
            "2": self.candidate_manager.view_all_candidates,
            "3": self.candidate_manager.update_candidate,
            "4": self.candidate_manager.delete_candidate,
            "5": self.candidate_manager.search_candidates,
            "6": self.station_manager.create_voting_station,
            "7": self.station_manager.view_all_stations,
            "8": self.station_manager.update_station,
            "9": self.station_manager.delete_station,
            "10": self.position_manager.create_position,
            "11": self.position_manager.view_positions,
            "12": self.position_manager.update_position,
            "13": self.position_manager.delete_position,
            "14": self.poll_manager.create_poll,
            "15": self.poll_manager.view_all_polls,
            "16": self.poll_manager.update_poll,
            "17": self.poll_manager.delete_poll,
            "18": self.poll_manager.open_close_poll,
            "19": self.poll_manager.assign_candidates_to_poll,
            "20": self.voter_manager.view_all_voters,
            "21": self.voter_manager.verify_voter,
            "22": self.voter_manager.deactivate_voter,
            "23": self.voter_manager.search_voters,
            "24": self.admin_account_manager.create_admin,
            "25": self.admin_account_manager.view_admins,
            "26": self.admin_account_manager.deactivate_admin,
            "27": self.reporting_service.view_poll_results,
            "28": self.reporting_service.view_detailed_statistics,
            "29": self.reporting_service.view_audit_log,
            "30": self.reporting_service.station_wise_results,
            self.SAVE_DATA_CHOICE: self._save_data,
            self.LOGOUT_CHOICE: self._logout,
        }

    def run(self):
        while True:
            ui.clear_screen()
            ui.header("ADMIN DASHBOARD", ui.THEME_ADMIN)
            print(
                f"  {ui.THEME_ADMIN}  ● {ui.RESET}{ui.BOLD}{self.current_user['full_name']}{ui.RESET}  "
                f"{ui.DIM}│  Role: {self.current_user['role']}{ui.RESET}"
            )

            ui.subheader("Candidate Management", ui.THEME_ADMIN_ACCENT)
            ui.menu_item(1, "Create Candidate", ui.THEME_ADMIN)
            ui.menu_item(2, "View All Candidates", ui.THEME_ADMIN)
            ui.menu_item(3, "Update Candidate", ui.THEME_ADMIN)
            ui.menu_item(4, "Delete Candidate", ui.THEME_ADMIN)
            ui.menu_item(5, "Search Candidates", ui.THEME_ADMIN)

            ui.subheader("Voting Station Management", ui.THEME_ADMIN_ACCENT)
            ui.menu_item(6, "Create Voting Station", ui.THEME_ADMIN)
            ui.menu_item(7, "View All Stations", ui.THEME_ADMIN)
            ui.menu_item(8, "Update Station", ui.THEME_ADMIN)
            ui.menu_item(9, "Delete Station", ui.THEME_ADMIN)

            ui.subheader("Polls & Positions", ui.THEME_ADMIN_ACCENT)
            ui.menu_item(10, "Create Position", ui.THEME_ADMIN)
            ui.menu_item(11, "View Positions", ui.THEME_ADMIN)
            ui.menu_item(12, "Update Position", ui.THEME_ADMIN)
            ui.menu_item(13, "Delete Position", ui.THEME_ADMIN)
            ui.menu_item(14, "Create Poll", ui.THEME_ADMIN)
            ui.menu_item(15, "View All Polls", ui.THEME_ADMIN)
            ui.menu_item(16, "Update Poll", ui.THEME_ADMIN)
            ui.menu_item(17, "Delete Poll", ui.THEME_ADMIN)
            ui.menu_item(18, "Open/Close Poll", ui.THEME_ADMIN)
            ui.menu_item(19, "Assign Candidates to Poll", ui.THEME_ADMIN)

            ui.subheader("Voter Management", ui.THEME_ADMIN_ACCENT)
            ui.menu_item(20, "View All Voters", ui.THEME_ADMIN)
            ui.menu_item(21, "Verify Voter", ui.THEME_ADMIN)
            ui.menu_item(22, "Deactivate Voter", ui.THEME_ADMIN)
            ui.menu_item(23, "Search Voters", ui.THEME_ADMIN)

            ui.subheader("Admin Management", ui.THEME_ADMIN_ACCENT)
            ui.menu_item(24, "Create Admin Account", ui.THEME_ADMIN)
            ui.menu_item(25, "View Admins", ui.THEME_ADMIN)
            ui.menu_item(26, "Deactivate Admin", ui.THEME_ADMIN)

            ui.subheader("Results & Reports", ui.THEME_ADMIN_ACCENT)
            ui.menu_item(27, "View Poll Results", ui.THEME_ADMIN)
            ui.menu_item(28, "View Detailed Statistics", ui.THEME_ADMIN)
            ui.menu_item(29, "View Audit Log", ui.THEME_ADMIN)
            ui.menu_item(30, "Station-wise Results", ui.THEME_ADMIN)

            ui.subheader("System", ui.THEME_ADMIN_ACCENT)
            ui.menu_item(31, "Save Data", ui.THEME_ADMIN)
            ui.menu_item(32, "Logout", ui.THEME_ADMIN)
            print()
            choice = ui.prompt("Enter choice: ")

            action = self._actions.get(choice)
            if action is None:
                ui.error("Invalid choice.")
                ui.pause()
                continue

            action()
            if choice == self.LOGOUT_CHOICE:
                break
