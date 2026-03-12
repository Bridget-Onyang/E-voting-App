import datetime
import hashlib
import random
import string
import json
import os
import time
import sys
from ui import *
from utils import *
from storage import *
from auth import *

if sys.platform == "win32":
    os.system("")

current_user = None

### voting process
def voter_dashboard():
    while True:
        clear_screen()
        header("VOTER DASHBOARD", THEME_VOTER)
        station_name = voting_stations.get(current_user["station_id"], {}).get("name", "Unknown")
        print(f"  {THEME_VOTER}  ● {RESET}{BOLD}{current_user['full_name']}{RESET}")
        print(f"  {DIM}    Card: {current_user['voter_card_number']}  │  Station: {station_name}{RESET}")
        print()
        menu_item(1, "View Open Polls", THEME_VOTER)
        menu_item(2, "Cast Vote", THEME_VOTER)
        menu_item(3, "View My Voting History", THEME_VOTER)
        menu_item(4, "View Results (Closed Polls)", THEME_VOTER)
        menu_item(5, "View My Profile", THEME_VOTER)
        menu_item(6, "Change Password", THEME_VOTER)
        menu_item(7, "Logout", THEME_VOTER)
        print()
        choice = prompt("Enter choice: ")
        if choice == "1": view_open_polls_voter()
        elif choice == "2": cast_vote()
        elif choice == "3": view_voting_history()
        elif choice == "4": view_closed_poll_results_voter()
        elif choice == "5": view_voter_profile()
        elif choice == "6": change_voter_password()
        elif choice == "7": log_action("LOGOUT", current_user["voter_card_number"], "Voter logged out"); save_data(); break
        else: error("Invalid choice."); pause()


def view_open_polls_voter():
    clear_screen()
    header("OPEN POLLS", THEME_VOTER)
    open_polls = {pid: p for pid, p in polls.items() if p["status"] == "open"}
    if not open_polls: print(); info("No open polls at this time."); pause(); return
    for pid, poll in open_polls.items():
        already_voted = pid in current_user.get("has_voted_in", [])
        vs = f" {GREEN}[VOTED]{RESET}" if already_voted else f" {YELLOW}[NOT YET VOTED]{RESET}"
        print(f"\n  {BOLD}{THEME_VOTER}Poll #{poll['id']}: {poll['title']}{RESET}{vs}")
        print(f"  {DIM}Type:{RESET} {poll['election_type']}  {DIM}│  Period:{RESET} {poll['start_date']} to {poll['end_date']}")
        for pos in poll["positions"]:
            print(f"    {THEME_VOTER_ACCENT}▸{RESET} {BOLD}{pos['position_title']}{RESET}")
            for ccid in pos["candidate_ids"]:
                if ccid in candidates:
                    c = candidates[ccid]
                    print(f"      {DIM}•{RESET} {c['full_name']} {DIM}({c['party']}) │ Age: {c['age']} │ Edu: {c['education']}{RESET}")
    pause()


def cast_vote():
    clear_screen()
    header("CAST YOUR VOTE", THEME_VOTER)
    open_polls = {pid: p for pid, p in polls.items() if p["status"] == "open"}
    if not open_polls: print(); info("No open polls at this time."); pause(); return
    available_polls = {}
    for pid, poll in open_polls.items():
        if pid not in current_user.get("has_voted_in", []) and current_user["station_id"] in poll["station_ids"]:
            available_polls[pid] = poll
    if not available_polls: print(); info("No available polls to vote in."); pause(); return
    subheader("Available Polls", THEME_VOTER_ACCENT)
    for pid, poll in available_polls.items():
        print(f"  {THEME_VOTER}{poll['id']}.{RESET} {poll['title']} {DIM}({poll['election_type']}){RESET}")
    try: pid = int(prompt("\nSelect Poll ID to vote: "))
    except ValueError: error("Invalid input."); pause(); return
    if pid not in available_polls: error("Invalid poll selection."); pause(); return
    poll = polls[pid]
    print()
    header(f"Voting: {poll['title']}", THEME_VOTER)
    info("Please select ONE candidate for each position.\n")
    my_votes = []
    for pos in poll["positions"]:
        subheader(pos['position_title'], THEME_VOTER_ACCENT)
        if not pos["candidate_ids"]: info("No candidates for this position."); continue
        for idx, ccid in enumerate(pos["candidate_ids"], 1):
            if ccid in candidates:
                c = candidates[ccid]
                print(f"    {THEME_VOTER}{BOLD}{idx}.{RESET} {c['full_name']} {DIM}({c['party']}){RESET}")
                print(f"       {DIM}Age: {c['age']} │ Edu: {c['education']} │ Exp: {c['years_experience']} yrs{RESET}")
                if c["manifesto"]: print(f"       {ITALIC}{DIM}{c['manifesto'][:80]}...{RESET}")
        print(f"    {GRAY}{BOLD}0.{RESET} {GRAY}Abstain / Skip{RESET}")
        try: vote_choice = int(prompt(f"\nYour choice for {pos['position_title']}: "))
        except ValueError: warning("Invalid input. Skipping."); vote_choice = 0
        if vote_choice == 0:
            my_votes.append({"position_id": pos["position_id"], "position_title": pos["position_title"], "candidate_id": None, "abstained": True})
        elif 1 <= vote_choice <= len(pos["candidate_ids"]):
            selected_cid = pos["candidate_ids"][vote_choice - 1]
            my_votes.append({"position_id": pos["position_id"], "position_title": pos["position_title"], "candidate_id": selected_cid, "candidate_name": candidates[selected_cid]["full_name"], "abstained": False})
        else:
            warning("Invalid choice. Marking as abstain.")
            my_votes.append({"position_id": pos["position_id"], "position_title": pos["position_title"], "candidate_id": None, "abstained": True})
    subheader("VOTE SUMMARY", BRIGHT_WHITE)
    for mv in my_votes:
        if mv["abstained"]: print(f"  {mv['position_title']}: {GRAY}ABSTAINED{RESET}")
        else: print(f"  {mv['position_title']}: {BRIGHT_GREEN}{BOLD}{mv['candidate_name']}{RESET}")
    print()
    if prompt("Confirm your votes? This cannot be undone. (yes/no): ").lower() != "yes": info("Vote cancelled."); pause(); return
    vote_timestamp = str(datetime.datetime.now())
    vote_hash = hashlib.sha256(f"{current_user['id']}{pid}{vote_timestamp}".encode()).hexdigest()[:16]
    for mv in my_votes:
        votes.append({"vote_id": vote_hash + str(mv["position_id"]), "poll_id": pid, "position_id": mv["position_id"], "candidate_id": mv["candidate_id"], "voter_id": current_user["id"], "station_id": current_user["station_id"], "timestamp": vote_timestamp, "abstained": mv["abstained"]})
    current_user["has_voted_in"].append(pid)
    for vid, v in voters.items():
        if v["id"] == current_user["id"]: v["has_voted_in"].append(pid); break
    polls[pid]["total_votes_cast"] += 1
    log_action("CAST_VOTE", current_user["voter_card_number"], f"Voted in poll: {poll['title']} (Hash: {vote_hash})")
    print()
    success("Your vote has been recorded successfully!")
    print(f"  {DIM}Vote Reference:{RESET} {BRIGHT_YELLOW}{vote_hash}{RESET}")
    print(f"  {BRIGHT_CYAN}Thank you for participating in the democratic process!{RESET}")
    save_data(); pause()


def view_voting_history():
    clear_screen()
    header("MY VOTING HISTORY", THEME_VOTER)
    voted_polls = current_user.get("has_voted_in", [])
    if not voted_polls: print(); info("You have not voted in any polls yet."); pause(); return
    print(f"\n  {DIM}You have voted in {len(voted_polls)} poll(s):{RESET}\n")
    for pid in voted_polls:
        if pid in polls:
            poll = polls[pid]
            sc = GREEN if poll['status'] == 'open' else RED
            print(f"  {BOLD}{THEME_VOTER}Poll #{pid}: {poll['title']}{RESET}")
            print(f"  {DIM}Type:{RESET} {poll['election_type']}  {DIM}│  Status:{RESET} {sc}{poll['status'].upper()}{RESET}")
            for vr in [v for v in votes if v["poll_id"] == pid and v["voter_id"] == current_user["id"]]:
                pos_title = next((pos["position_title"] for pos in poll.get("positions", []) if pos["position_id"] == vr["position_id"]), "Unknown")
                if vr["abstained"]: print(f"    {THEME_VOTER_ACCENT}▸{RESET} {pos_title}: {GRAY}ABSTAINED{RESET}")
                else: print(f"    {THEME_VOTER_ACCENT}▸{RESET} {pos_title}: {BRIGHT_GREEN}{candidates.get(vr['candidate_id'], {}).get('full_name', 'Unknown')}{RESET}")
            print()
    pause()


def view_closed_poll_results_voter():
    clear_screen()
    header("ELECTION RESULTS", THEME_VOTER)
    closed_polls = {pid: p for pid, p in polls.items() if p["status"] == "closed"}
    if not closed_polls: print(); info("No closed polls with results."); pause(); return
    for pid, poll in closed_polls.items():
        print(f"\n  {BOLD}{THEME_VOTER}{poll['title']}{RESET}")
        print(f"  {DIM}Type:{RESET} {poll['election_type']}  {DIM}│  Votes:{RESET} {poll['total_votes_cast']}")
        for pos in poll["positions"]:
            subheader(pos['position_title'], THEME_VOTER_ACCENT)
            vote_counts = {}
            abstain_count = 0
            for v in votes:
                if v["poll_id"] == pid and v["position_id"] == pos["position_id"]:
                    if v["abstained"]: abstain_count += 1
                    else: vote_counts[v["candidate_id"]] = vote_counts.get(v["candidate_id"], 0) + 1
            total = sum(vote_counts.values()) + abstain_count
            for rank, (cid, count) in enumerate(sorted(vote_counts.items(), key=lambda x: x[1], reverse=True), 1):
                cand = candidates.get(cid, {})
                pct = (count / total * 100) if total > 0 else 0
                bar = f"{THEME_VOTER}{'█' * int(pct / 2)}{GRAY}{'░' * (50 - int(pct / 2))}{RESET}"
                winner = f" {BG_GREEN}{BLACK}{BOLD} WINNER {RESET}" if rank <= pos["max_winners"] else ""
                print(f"    {BOLD}{rank}. {cand.get('full_name', '?')}{RESET} {DIM}({cand.get('party', '?')}){RESET}")
                print(f"       {bar} {BOLD}{count}{RESET} ({pct:.1f}%){winner}")
            if abstain_count > 0:
                print(f"    {GRAY}Abstained: {abstain_count} ({(abstain_count / total * 100) if total > 0 else 0:.1f}%){RESET}")
    pause()


def view_voter_profile():
    clear_screen()
    header("MY PROFILE", THEME_VOTER)
    v = current_user
    station_name = voting_stations.get(v["station_id"], {}).get("name", "Unknown")
    print()
    for label, value in [
        ("Name", v['full_name']), ("National ID", v['national_id']),
        ("Voter Card", f"{BRIGHT_YELLOW}{v['voter_card_number']}{RESET}"),
        ("Date of Birth", v['date_of_birth']), ("Age", v['age']), ("Gender", v['gender']),
        ("Address", v['address']), ("Phone", v['phone']), ("Email", v['email']),
        ("Station", station_name),
        ("Verified", status_badge('Yes', True) if v['is_verified'] else status_badge('No', False)),
        ("Registered", v['registered_at']), ("Polls Voted", len(v.get('has_voted_in', [])))
    ]:
        print(f"  {THEME_VOTER}{label + ':':<16}{RESET} {value}")
    pause()


def change_voter_password():
    clear_screen()
    header("CHANGE PASSWORD", THEME_VOTER)
    print()
    old_pass = masked_input("Current Password: ").strip()
    if hash_password(old_pass) != current_user["password"]: error("Incorrect current password."); pause(); return
    new_pass = masked_input("New Password: ").strip()
    if len(new_pass) < 6: error("Password must be at least 6 characters."); pause(); return
    confirm_pass = masked_input("Confirm New Password: ").strip()
    if new_pass != confirm_pass: error("Passwords do not match."); pause(); return
    current_user["password"] = hash_password(new_pass)
    for vid, v in voters.items():
        if v["id"] == current_user["id"]: v["password"] = hash_password(new_pass); break
    log_action("CHANGE_PASSWORD", current_user["voter_card_number"], "Password changed")
    print(); success("Password changed successfully!")
    save_data(); pause()


### results and stats
def view_poll_results():
    clear_screen()
    header("POLL RESULTS", THEME_ADMIN)
    if not polls: print(); info("No polls found."); pause(); return
    print()
    for pid, poll in polls.items():
        sc = GREEN if poll['status'] == 'open' else (YELLOW if poll['status'] == 'draft' else RED)
        print(f"  {THEME_ADMIN}{poll['id']}.{RESET} {poll['title']} {sc}({poll['status']}){RESET}")
    try: pid = int(prompt("\nEnter Poll ID: "))
    except ValueError: error("Invalid input."); pause(); return
    if pid not in polls: error("Poll not found."); pause(); return
    poll = polls[pid]
    print()
    header(f"RESULTS: {poll['title']}", THEME_ADMIN)
    sc = GREEN if poll['status'] == 'open' else RED
    print(f"  {DIM}Status:{RESET} {sc}{BOLD}{poll['status'].upper()}{RESET}  {DIM}│  Votes:{RESET} {BOLD}{poll['total_votes_cast']}{RESET}")
    total_eligible = sum(1 for v in voters.values() if v["is_verified"] and v["is_active"] and v["station_id"] in poll["station_ids"])
    turnout = (poll['total_votes_cast'] / total_eligible * 100) if total_eligible > 0 else 0
    tc = GREEN if turnout > 50 else (YELLOW if turnout > 25 else RED)
    print(f"  {DIM}Eligible:{RESET} {total_eligible}  {DIM}│  Turnout:{RESET} {tc}{BOLD}{turnout:.1f}%{RESET}")
    for pos in poll["positions"]:
        subheader(f"{pos['position_title']} (Seats: {pos['max_winners']})", THEME_ADMIN_ACCENT)
        vote_counts = {}
        abstain_count = 0
        total_pos = 0
        for v in votes:
            if v["poll_id"] == pid and v["position_id"] == pos["position_id"]:
                total_pos += 1
                if v["abstained"]: abstain_count += 1
                else: vote_counts[v["candidate_id"]] = vote_counts.get(v["candidate_id"], 0) + 1
        for rank, (cid, count) in enumerate(sorted(vote_counts.items(), key=lambda x: x[1], reverse=True), 1):
            cand = candidates.get(cid, {})
            pct = (count / total_pos * 100) if total_pos > 0 else 0
            bl = int(pct / 2)
            bar = f"{THEME_ADMIN}{'█' * bl}{GRAY}{'░' * (50 - bl)}{RESET}"
            winner = f" {BG_GREEN}{BLACK}{BOLD} ★ WINNER {RESET}" if rank <= pos["max_winners"] else ""
            print(f"    {BOLD}{rank}. {cand.get('full_name', '?')}{RESET} {DIM}({cand.get('party', '?')}){RESET}")
            print(f"       {bar} {BOLD}{count}{RESET} ({pct:.1f}%){winner}")
        if abstain_count > 0: print(f"    {GRAY}Abstained: {abstain_count} ({(abstain_count / total_pos * 100) if total_pos > 0 else 0:.1f}%){RESET}")
        if not vote_counts: info("    No votes recorded for this position.")
    pause()


def view_detailed_statistics():
    clear_screen()
    header("DETAILED STATISTICS", THEME_ADMIN)
    subheader("SYSTEM OVERVIEW", THEME_ADMIN_ACCENT)
    tc = len(candidates); ac = sum(1 for c in candidates.values() if c["is_active"])
    tv = len(voters); vv = sum(1 for v in voters.values() if v["is_verified"])
    av = sum(1 for v in voters.values() if v["is_active"])
    ts = len(voting_stations); ast = sum(1 for s in voting_stations.values() if s["is_active"])
    tp = len(polls)
    op = sum(1 for p in polls.values() if p["status"] == "open")
    cp = sum(1 for p in polls.values() if p["status"] == "closed")
    dp = sum(1 for p in polls.values() if p["status"] == "draft")
    print(f"  {THEME_ADMIN}Candidates:{RESET}  {tc} {DIM}(Active: {ac}){RESET}")
    print(f"  {THEME_ADMIN}Voters:{RESET}      {tv} {DIM}(Verified: {vv}, Active: {av}){RESET}")
    print(f"  {THEME_ADMIN}Stations:{RESET}    {ts} {DIM}(Active: {ast}){RESET}")
    print(f"  {THEME_ADMIN}Polls:{RESET}       {tp} {DIM}({GREEN}Open: {op}{RESET}{DIM}, {RED}Closed: {cp}{RESET}{DIM}, {YELLOW}Draft: {dp}{RESET}{DIM}){RESET}")
    print(f"  {THEME_ADMIN}Total Votes:{RESET} {len(votes)}")
    subheader("VOTER DEMOGRAPHICS", THEME_ADMIN_ACCENT)
    gender_counts = {}
    age_groups = {"18-25": 0, "26-35": 0, "36-45": 0, "46-55": 0, "56-65": 0, "65+": 0}
    for v in voters.values():
        gender_counts[v.get("gender", "?")] = gender_counts.get(v.get("gender", "?"), 0) + 1
        age = v.get("age", 0)
        if age <= 25: age_groups["18-25"] += 1
        elif age <= 35: age_groups["26-35"] += 1
        elif age <= 45: age_groups["36-45"] += 1
        elif age <= 55: age_groups["46-55"] += 1
        elif age <= 65: age_groups["56-65"] += 1
        else: age_groups["65+"] += 1
    for g, count in gender_counts.items():
        pct = (count / tv * 100) if tv > 0 else 0
        print(f"    {g}: {count} ({pct:.1f}%)")
    print(f"  {BOLD}Age Distribution:{RESET}")
    for group, count in age_groups.items():
        pct = (count / tv * 100) if tv > 0 else 0
        print(f"    {group:>5}: {count:>3} ({pct:>5.1f}%) {THEME_ADMIN}{'█' * int(pct / 2)}{RESET}")
    subheader("STATION LOAD", THEME_ADMIN_ACCENT)
    for sid, s in voting_stations.items():
        vc = sum(1 for v in voters.values() if v["station_id"] == sid)
        lp = (vc / s["capacity"] * 100) if s["capacity"] > 0 else 0
        lc = RED if lp > 100 else (YELLOW if lp > 75 else GREEN)
        st = f"{RED}{BOLD}OVERLOADED{RESET}" if lp > 100 else f"{GREEN}OK{RESET}"
        print(f"    {s['name']}: {vc}/{s['capacity']} {lc}({lp:.0f}%){RESET} {st}")
    subheader("CANDIDATE PARTY DISTRIBUTION", THEME_ADMIN_ACCENT)
    party_counts = {}
    for c in candidates.values():
        if c["is_active"]: party_counts[c["party"]] = party_counts.get(c["party"], 0) + 1
    for party, count in sorted(party_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"    {party}: {BOLD}{count}{RESET} candidate(s)")
    subheader("CANDIDATE EDUCATION LEVELS", THEME_ADMIN_ACCENT)
    edu_counts = {}
    for c in candidates.values():
        if c["is_active"]: edu_counts[c["education"]] = edu_counts.get(c["education"], 0) + 1
    for edu, count in edu_counts.items():
        print(f"    {edu}: {BOLD}{count}{RESET}")
    pause()


def station_wise_results():
    clear_screen()
    header("STATION-WISE RESULTS", THEME_ADMIN)
    if not polls: print(); info("No polls found."); pause(); return
    print()
    for pid, poll in polls.items():
        sc = GREEN if poll['status'] == 'open' else (YELLOW if poll['status'] == 'draft' else RED)
        print(f"  {THEME_ADMIN}{poll['id']}.{RESET} {poll['title']} {sc}({poll['status']}){RESET}")
    try: pid = int(prompt("\nEnter Poll ID: "))
    except ValueError: error("Invalid input."); pause(); return
    if pid not in polls: error("Poll not found."); pause(); return
    poll = polls[pid]
    print()
    header(f"STATION RESULTS: {poll['title']}", THEME_ADMIN)
    for sid in poll["station_ids"]:
        if sid not in voting_stations: continue
        station = voting_stations[sid]
        subheader(f"{station['name']}  ({station['location']})", BRIGHT_WHITE)
        station_votes = [v for v in votes if v["poll_id"] == pid and v["station_id"] == sid]
        svc = len(set(v["voter_id"] for v in station_votes))
        ras = sum(1 for v in voters.values() if v["station_id"] == sid and v["is_verified"] and v["is_active"])
        st = (svc / ras * 100) if ras > 0 else 0
        tc = GREEN if st > 50 else (YELLOW if st > 25 else RED)
        print(f"  {DIM}Registered:{RESET} {ras}  {DIM}│  Voted:{RESET} {svc}  {DIM}│  Turnout:{RESET} {tc}{BOLD}{st:.1f}%{RESET}")
        for pos in poll["positions"]:
            print(f"    {THEME_ADMIN_ACCENT}▸ {pos['position_title']}:{RESET}")
            pv = [v for v in station_votes if v["position_id"] == pos["position_id"]]
            vc = {}; ac = 0
            for v in pv:
                if v["abstained"]: ac += 1
                else: vc[v["candidate_id"]] = vc.get(v["candidate_id"], 0) + 1
            total = sum(vc.values()) + ac
            for cid, count in sorted(vc.items(), key=lambda x: x[1], reverse=True):
                cand = candidates.get(cid, {})
                pct = (count / total * 100) if total > 0 else 0
                print(f"      {cand.get('full_name', '?')} {DIM}({cand.get('party', '?')}){RESET}: {BOLD}{count}{RESET} ({pct:.1f}%)")
            if ac > 0: print(f"      {GRAY}Abstained: {ac} ({(ac / total * 100) if total > 0 else 0:.1f}%){RESET}")
    pause()


def view_audit_log():
    clear_screen()
    header("AUDIT LOG", THEME_ADMIN)
    if not audit_log: print(); info("No audit records."); pause(); return
    print(f"\n  {DIM}Total Records: {len(audit_log)}{RESET}")
    subheader("Filter", THEME_ADMIN_ACCENT)
    menu_item(1, "Last 20 entries", THEME_ADMIN); menu_item(2, "All entries", THEME_ADMIN)
    menu_item(3, "Filter by action type", THEME_ADMIN); menu_item(4, "Filter by user", THEME_ADMIN)
    choice = prompt("\nChoice: ")
    entries = audit_log
    if choice == "1": entries = audit_log[-20:]
    elif choice == "3":
        action_types = list(set(e["action"] for e in audit_log))
        for i, at in enumerate(action_types, 1): print(f"    {THEME_ADMIN}{i}.{RESET} {at}")
        try: at_choice = int(prompt("Select action type: ")); entries = [e for e in audit_log if e["action"] == action_types[at_choice - 1]]
        except (ValueError, IndexError): error("Invalid choice."); pause(); return
    elif choice == "4":
        uf = prompt("Enter username/card number: ")
        entries = [e for e in audit_log if uf.lower() in e["user"].lower()]
    print()
    table_header(f"{'Timestamp':<22} {'Action':<25} {'User':<20} {'Details'}", THEME_ADMIN)
    table_divider(100, THEME_ADMIN)
    for entry in entries:
        ac = GREEN if "CREATE" in entry["action"] or entry["action"] == "LOGIN" else (RED if "DELETE" in entry["action"] or "DEACTIVATE" in entry["action"] else (YELLOW if "UPDATE" in entry["action"] else RESET))
        print(f"  {DIM}{entry['timestamp'][:19]}{RESET}  {ac}{entry['action']:<25}{RESET} {entry['user']:<20} {DIM}{entry['details'][:50]}{RESET}")
    pause()
