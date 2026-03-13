import sys

import storage
import ui
from auth_service import AuthService
from candidate_service import CandidateService
from poll_service import PollService
from position_service import PositionService
from station_service import StationService
from user_admin_service import VoterAdministrationService
from voter_portal import VoterPortal


class InputFeeder:
    def __init__(self):
        self.items = []

    def push(self, *values):
        self.items.extend(values)

    def pop(self, label):
        if not self.items:
            raise RuntimeError(f"No queued input left for: {label}")
        return self.items.pop(0)


def run_flow_check():
    feeder = InputFeeder()
    messages = []

    originals = {
        "prompt": ui.prompt,
        "masked_input": ui.masked_input,
        "pause": ui.pause,
        "clear_screen": ui.clear_screen,
        "header": ui.header,
        "subheader": ui.subheader,
        "menu_item": ui.menu_item,
        "error": ui.error,
        "warning": ui.warning,
        "info": ui.info,
        "success": ui.success,
        "save_data": storage.save_data,
    }

    ui.prompt = lambda label="": feeder.pop(label)
    ui.masked_input = lambda label="": feeder.pop(label)
    ui.pause = lambda: None
    ui.clear_screen = lambda: None
    ui.header = lambda *args, **kwargs: None
    ui.subheader = lambda *args, **kwargs: None
    ui.menu_item = lambda *args, **kwargs: None
    ui.error = lambda text: messages.append(("error", text))
    ui.warning = lambda text: messages.append(("warning", text))
    ui.info = lambda text: messages.append(("info", text))
    ui.success = lambda text: messages.append(("success", text))
    storage.save_data = lambda: None

    try:
        storage.candidates.clear()
        storage.voting_stations.clear()
        storage.polls.clear()
        storage.positions.clear()
        storage.voters.clear()
        storage.admins.clear()
        storage.votes.clear()
        storage.audit_log.clear()

        storage.candidate_id_counter = 1
        storage.station_id_counter = 1
        storage.poll_id_counter = 1
        storage.position_id_counter = 1
        storage.voter_id_counter = 1
        storage.admin_id_counter = 1

        storage._seed_default_admin()

        auth = AuthService()

        feeder.push("admin", "admin123")
        admin_user, admin_role = auth._login_admin()
        assert admin_user is not None and admin_role == "admin", "Admin login failed"

        station_service = StationService()
        station_service.set_current_user(admin_user)
        feeder.push(
            "Central Station",
            "Main Street",
            "North District",
            "500",
            "Jane Supervisor",
            "0700000000",
            "08:00",
            "17:00",
        )
        station_service.create_voting_station()
        assert len(storage.voting_stations) == 1, "Station creation failed"
        station_id = next(iter(storage.voting_stations.keys()))

        feeder.push(
            "John Voter",
            "NID123456",
            "1995-05-12",
            "M",
            "Some Address",
            "0711111111",
            "john@example.com",
            "voter123",
            "voter123",
            str(station_id),
        )
        auth.register_voter()
        assert len(storage.voters) == 1, "Voter registration failed"
        voter_id = next(iter(storage.voters.keys()))
        voter = storage.voters[voter_id]
        assert voter["station_id"] == station_id, "Voter station assignment failed"

        voter_admin = VoterAdministrationService()
        voter_admin.set_current_user(admin_user)
        feeder.push("1", str(voter_id))
        voter_admin.verify_voter()
        assert storage.voters[voter_id]["is_verified"] is True, "Voter verification failed"

        position_service = PositionService()
        position_service.set_current_user(admin_user)
        feeder.push("President", "National leadership", "National", "1", "25")
        position_service.create_position()
        assert len(storage.positions) == 1, "Position creation failed"

        candidate_service = CandidateService()
        candidate_service.set_current_user(admin_user)
        feeder.push(
            "Alice Candidate",
            "CAND001",
            "1980-03-10",
            "F",
            "1",
            "Unity Party",
            "Better governance",
            "Candidate Address",
            "0722222222",
            "alice@party.com",
            "no",
            "10",
        )
        candidate_service.create_candidate()
        assert len(storage.candidates) == 1, "Candidate creation failed"

        poll_service = PollService()
        poll_service.set_current_user(admin_user)
        feeder.push(
            "General Election 2026",
            "National general election",
            "General",
            "2026-01-01",
            "2026-12-31",
            "1",
            "yes",
        )
        poll_service.create_poll()
        assert len(storage.polls) == 1, "Poll creation failed"
        poll_id = next(iter(storage.polls.keys()))

        feeder.push(str(poll_id), "yes", "1")
        poll_service.assign_candidates_to_poll()
        assert storage.polls[poll_id]["positions"][0]["candidate_ids"] == [1], "Candidate assignment failed"

        feeder.push(str(poll_id), "yes")
        poll_service.open_close_poll()
        assert storage.polls[poll_id]["status"] == "open", "Poll open failed"

        voter_card = storage.voters[voter_id]["voter_card_number"]
        feeder.push(voter_card, "voter123")
        voter_user, voter_role = auth._login_voter()
        assert voter_user is not None and voter_role == "voter", "Voter login failed"

        portal = VoterPortal()
        portal.set_current_user(voter_user)
        feeder.push(str(poll_id), "1", "yes")
        portal.cast_vote()

        assert len(storage.votes) == 1, "Vote record not created"
        assert storage.polls[poll_id]["total_votes_cast"] == 1, "Poll vote tally not updated"
        assert poll_id in storage.voters[voter_id]["has_voted_in"], "Voter history not updated"

        print("INTEGRATION_CHECK: PASS")
        print(f"ADMIN_LOGIN: PASS username={admin_user['username']}")
        print(f"STATION_REGISTER: PASS station_id={station_id}")
        print(f"VOTER_REGISTER_AND_STATION_ASSIGN: PASS voter_id={voter_id} station_id={voter['station_id']}")
        print(f"VOTER_LOGIN: PASS card={voter_card}")
        print(f"CAST_VOTE: PASS poll_id={poll_id} total_votes={len(storage.votes)}")
        print(f"UI_ERRORS_CAPTURED: {sum(1 for kind, _ in messages if kind == 'error')}")
        return 0

    except Exception as exc:
        print("INTEGRATION_CHECK: FAIL")
        print(f"{type(exc).__name__}: {exc}")
        if messages:
            print("RECENT_UI_MESSAGES:")
            for kind, text in messages[-8:]:
                print(f"- {kind}: {text}")
        return 1

    finally:
        ui.prompt = originals["prompt"]
        ui.masked_input = originals["masked_input"]
        ui.pause = originals["pause"]
        ui.clear_screen = originals["clear_screen"]
        ui.header = originals["header"]
        ui.subheader = originals["subheader"]
        ui.menu_item = originals["menu_item"]
        ui.error = originals["error"]
        ui.warning = originals["warning"]
        ui.info = originals["info"]
        ui.success = originals["success"]
        storage.save_data = originals["save_data"]


if __name__ == "__main__":
    raise SystemExit(run_flow_check())
