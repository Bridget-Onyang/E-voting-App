import datetime

import storage
import ui
import utils
from service_base import UserBoundService


class PositionService(UserBoundService):
    VALID_LEVELS = {"national", "regional", "local"}
    YES_VALUE = "yes"

    @staticmethod
    def _show_positions_for_selection():
        for position in storage.positions.values():
            print(
                f"  {ui.THEME_ADMIN}{position['id']}.{ui.RESET} {position['title']} "
                f"{ui.DIM}({position['level']}){ui.RESET}"
            )

    @staticmethod
    def _is_in_open_poll(position_id):
        for poll in storage.polls.values():
            for poll_position in poll.get("positions", []):
                if poll_position["position_id"] == position_id and poll["status"] == "open":
                    return poll["title"]
        return None

    def create_position(self):
        ui.clear_screen()
        ui.header("CREATE POSITION", ui.THEME_ADMIN)
        print()
        title = ui.prompt("Position Title (e.g. President, Governor, Senator): ")
        if not title:
            ui.error("Title cannot be empty.")
            ui.pause()
            return

        description = ui.prompt("Description: ")
        level = ui.prompt("Level (National/Regional/Local): ")
        if level.lower() not in self.VALID_LEVELS:
            ui.error("Invalid level.")
            ui.pause()
            return

        try:
            max_winners = int(ui.prompt("Number of winners/seats: "))
            if max_winners <= 0:
                ui.error("Must be at least 1.")
                ui.pause()
                return
        except ValueError:
            ui.error("Invalid number.")
            ui.pause()
            return

        min_candidate_age = ui.prompt(f"Minimum candidate age [{storage.MIN_CANDIDATE_AGE}]: ")
        min_candidate_age = (
            int(min_candidate_age) if min_candidate_age.isdigit() else storage.MIN_CANDIDATE_AGE
        )

        position_id = storage.position_id_counter
        storage.positions[position_id] = {
            "id": position_id,
            "title": title,
            "description": description,
            "level": level.capitalize(),
            "max_winners": max_winners,
            "min_candidate_age": min_candidate_age,
            "is_active": True,
            "created_at": str(datetime.datetime.now()),
            "created_by": self.current_user["username"],
        }
        utils.log_action(
            "CREATE_POSITION",
            self.current_user["username"],
            f"Created position: {title} (ID: {position_id})",
        )
        print()
        ui.success(f"Position '{title}' created! ID: {position_id}")
        storage.position_id_counter += 1
        storage.save_data()
        ui.pause()

    def view_positions(self):
        ui.clear_screen()
        ui.header("ALL POSITIONS", ui.THEME_ADMIN)
        if not storage.positions:
            print()
            ui.info("No positions found.")
            ui.pause()
            return

        print()
        ui.table_header(
            f"{'ID':<5} {'Title':<25} {'Level':<12} {'Seats':<8} {'Min Age':<10} {'Status':<10}",
            ui.THEME_ADMIN,
        )
        ui.table_divider(70, ui.THEME_ADMIN)
        for position in storage.positions.values():
            status = (
                ui.status_badge("Active", True)
                if position["is_active"]
                else ui.status_badge("Inactive", False)
            )
            print(
                f"  {position['id']:<5} {position['title']:<25} {position['level']:<12} "
                f"{position['max_winners']:<8} {position['min_candidate_age']:<10} {status}"
            )
        print(f"\n  {ui.DIM}Total Positions: {len(storage.positions)}{ui.RESET}")
        ui.pause()

    def update_position(self):
        ui.clear_screen()
        ui.header("UPDATE POSITION", ui.THEME_ADMIN)
        if not storage.positions:
            print()
            ui.info("No positions found.")
            ui.pause()
            return

        print()
        self._show_positions_for_selection()
        try:
            position_id = int(ui.prompt("\nEnter Position ID to update: "))
        except ValueError:
            ui.error("Invalid input.")
            ui.pause()
            return

        if position_id not in storage.positions:
            ui.error("Position not found.")
            ui.pause()
            return

        position = storage.positions[position_id]
        print(f"\n  {ui.BOLD}Updating: {position['title']}{ui.RESET}")
        ui.info("Press Enter to keep current value\n")
        new_title = ui.prompt(f"Title [{position['title']}]: ")
        if new_title:
            position["title"] = new_title
        new_description = ui.prompt(f"Description [{position['description'][:50]}]: ")
        if new_description:
            position["description"] = new_description
        new_level = ui.prompt(f"Level [{position['level']}]: ")
        if new_level and new_level.lower() in self.VALID_LEVELS:
            position["level"] = new_level.capitalize()
        new_seats = ui.prompt(f"Seats [{position['max_winners']}]: ")
        if new_seats:
            try:
                position["max_winners"] = int(new_seats)
            except ValueError:
                ui.warning("Keeping old value.")

        utils.log_action(
            "UPDATE_POSITION",
            self.current_user["username"],
            f"Updated position: {position['title']}",
        )
        print()
        ui.success("Position updated!")
        storage.save_data()
        ui.pause()

    def delete_position(self):
        ui.clear_screen()
        ui.header("DELETE POSITION", ui.THEME_ADMIN)
        if not storage.positions:
            print()
            ui.info("No positions found.")
            ui.pause()
            return

        print()
        self._show_positions_for_selection()
        try:
            position_id = int(ui.prompt("\nEnter Position ID to delete: "))
        except ValueError:
            ui.error("Invalid input.")
            ui.pause()
            return

        if position_id not in storage.positions:
            ui.error("Position not found.")
            ui.pause()
            return

        open_poll_title = self._is_in_open_poll(position_id)
        if open_poll_title is not None:
            ui.error(f"Cannot delete - in active poll: {open_poll_title}")
            ui.pause()
            return

        position_title = storage.positions[position_id]["title"]
        if ui.prompt(f"Confirm deactivation of '{position_title}'? (yes/no): ").lower() == self.YES_VALUE:
            storage.positions[position_id]["is_active"] = False
            utils.log_action(
                "DELETE_POSITION",
                self.current_user["username"],
                f"Deactivated position: {position_title}",
            )
            print()
            ui.success("Position deactivated.")
            storage.save_data()
        ui.pause()
