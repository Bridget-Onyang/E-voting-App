import time

import auth
import admin_business
import storage
import ui
import voter_business


LOADING_DELAY_SECONDS = 1


def _reset_session():
    admin_business.set_current_user(None)
    voter_business.set_current_user(None)
    storage.current_user = None
    storage.current_role = None


def main():
    """Run the interactive console application loop."""
    print(f"\n  {ui.THEME_LOGIN}Loading E-Voting System...{ui.RESET}")
    storage.load_data()
    time.sleep(LOADING_DELAY_SECONDS)

    while True:
        ui.clear_screen()
        user, role = auth.login()

        if user is None:
            continue

        storage.current_user = user
        storage.current_role = role

        admin_business.set_current_user(user)
        voter_business.set_current_user(user)

        if role == "admin":
            admin_business.admin_dashboard()
        elif role == "voter":
            voter_business.voter_dashboard()

        _reset_session()


if __name__ == "__main__":
    main()