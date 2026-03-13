import datetime

import storage
import ui
import utils
from service_base import UserBoundService


class StationService(UserBoundService):
    YES_VALUE = "yes"

    @staticmethod
    def _show_stations_for_selection():
        for station in storage.voting_stations.values():
            print(
                f"  {ui.THEME_ADMIN}{station['id']}.{ui.RESET} {station['name']} "
                f"{ui.DIM}- {station['location']}{ui.RESET}"
            )

    @staticmethod
    def _registered_voters_for_station(station_id):
        return sum(1 for voter in storage.voters.values() if voter["station_id"] == station_id)

    def create_voting_station(self):
        ui.clear_screen()
        ui.header("CREATE VOTING STATION", ui.THEME_ADMIN)
        print()
        name = ui.prompt("Station Name: ")
        if not name:
            ui.error("Name cannot be empty.")
            ui.pause()
            return

        location = ui.prompt("Location/Address: ")
        if not location:
            ui.error("Location cannot be empty.")
            ui.pause()
            return

        region = ui.prompt("Region/District: ")
        try:
            capacity = int(ui.prompt("Voter Capacity: "))
            if capacity <= 0:
                ui.error("Capacity must be positive.")
                ui.pause()
                return
        except ValueError:
            ui.error("Invalid capacity.")
            ui.pause()
            return

        supervisor = ui.prompt("Station Supervisor Name: ")
        contact = ui.prompt("Contact Phone: ")
        opening_time = ui.prompt("Opening Time (e.g. 08:00): ")
        closing_time = ui.prompt("Closing Time (e.g. 17:00): ")

        station_id = storage.station_id_counter
        storage.voting_stations[station_id] = {
            "id": station_id,
            "name": name,
            "location": location,
            "region": region,
            "capacity": capacity,
            "registered_voters": 0,
            "supervisor": supervisor,
            "contact": contact,
            "opening_time": opening_time,
            "closing_time": closing_time,
            "is_active": True,
            "created_at": str(datetime.datetime.now()),
            "created_by": self.current_user["username"],
        }
        utils.log_action(
            "CREATE_STATION",
            self.current_user["username"],
            f"Created station: {name} (ID: {station_id})",
        )
        print()
        ui.success(f"Voting Station '{name}' created! ID: {station_id}")
        storage.station_id_counter += 1
        storage.save_data()
        ui.pause()

    def view_all_stations(self):
        ui.clear_screen()
        ui.header("ALL VOTING STATIONS", ui.THEME_ADMIN)
        if not storage.voting_stations:
            print()
            ui.info("No voting stations found.")
            ui.pause()
            return

        print()
        ui.table_header(
            f"{'ID':<5} {'Name':<25} {'Location':<25} {'Region':<15} {'Cap.':<8} {'Reg.':<8} {'Status':<10}",
            ui.THEME_ADMIN,
        )
        ui.table_divider(96, ui.THEME_ADMIN)
        for station_id, station in storage.voting_stations.items():
            registered_count = self._registered_voters_for_station(station_id)
            status = (
                ui.status_badge("Active", True)
                if station["is_active"]
                else ui.status_badge("Inactive", False)
            )
            print(
                f"  {station['id']:<5} {station['name']:<25} {station['location']:<25} "
                f"{station['region']:<15} {station['capacity']:<8} {registered_count:<8} {status}"
            )
        print(f"\n  {ui.DIM}Total Stations: {len(storage.voting_stations)}{ui.RESET}")
        ui.pause()

    def update_station(self):
        ui.clear_screen()
        ui.header("UPDATE VOTING STATION", ui.THEME_ADMIN)
        if not storage.voting_stations:
            print()
            ui.info("No stations found.")
            ui.pause()
            return

        print()
        self._show_stations_for_selection()
        try:
            station_id = int(ui.prompt("\nEnter Station ID to update: "))
        except ValueError:
            ui.error("Invalid input.")
            ui.pause()
            return

        if station_id not in storage.voting_stations:
            ui.error("Station not found.")
            ui.pause()
            return

        station = storage.voting_stations[station_id]
        print(f"\n  {ui.BOLD}Updating: {station['name']}{ui.RESET}")
        ui.info("Press Enter to keep current value\n")
        new_name = ui.prompt(f"Name [{station['name']}]: ")
        if new_name:
            station["name"] = new_name
        new_location = ui.prompt(f"Location [{station['location']}]: ")
        if new_location:
            station["location"] = new_location
        new_region = ui.prompt(f"Region [{station['region']}]: ")
        if new_region:
            station["region"] = new_region
        new_capacity = ui.prompt(f"Capacity [{station['capacity']}]: ")
        if new_capacity:
            try:
                station["capacity"] = int(new_capacity)
            except ValueError:
                ui.warning("Invalid number, keeping old value.")
        new_supervisor = ui.prompt(f"Supervisor [{station['supervisor']}]: ")
        if new_supervisor:
            station["supervisor"] = new_supervisor
        new_contact = ui.prompt(f"Contact [{station['contact']}]: ")
        if new_contact:
            station["contact"] = new_contact

        utils.log_action(
            "UPDATE_STATION",
            self.current_user["username"],
            f"Updated station: {station['name']} (ID: {station_id})",
        )
        print()
        ui.success(f"Station '{station['name']}' updated successfully!")
        storage.save_data()
        ui.pause()

    def delete_station(self):
        ui.clear_screen()
        ui.header("DELETE VOTING STATION", ui.THEME_ADMIN)
        if not storage.voting_stations:
            print()
            ui.info("No stations found.")
            ui.pause()
            return

        print()
        for station in storage.voting_stations.values():
            status = (
                ui.status_badge("Active", True)
                if station["is_active"]
                else ui.status_badge("Inactive", False)
            )
            print(
                f"  {ui.THEME_ADMIN}{station['id']}.{ui.RESET} {station['name']} "
                f"{ui.DIM}({station['location']}){ui.RESET} {status}"
            )
        try:
            station_id = int(ui.prompt("\nEnter Station ID to delete: "))
        except ValueError:
            ui.error("Invalid input.")
            ui.pause()
            return

        if station_id not in storage.voting_stations:
            ui.error("Station not found.")
            ui.pause()
            return

        voter_count = self._registered_voters_for_station(station_id)
        if voter_count > 0:
            ui.warning(f"{voter_count} voters are registered at this station.")
            if ui.prompt("Proceed with deactivation? (yes/no): ").lower() != self.YES_VALUE:
                ui.info("Cancelled.")
                ui.pause()
                return

        station_name = storage.voting_stations[station_id]["name"]
        if ui.prompt(f"Confirm deactivation of '{station_name}'? (yes/no): ").lower() == self.YES_VALUE:
            storage.voting_stations[station_id]["is_active"] = False
            utils.log_action(
                "DELETE_STATION",
                self.current_user["username"],
                f"Deactivated station: {station_name}",
            )
            print()
            ui.success(f"Station '{station_name}' deactivated.")
            storage.save_data()
        else:
            ui.info("Cancelled.")
        ui.pause()
