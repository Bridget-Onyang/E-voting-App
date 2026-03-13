from voter_portal import VoterPortal


_portal = VoterPortal()


def set_current_user(user):
    _portal.set_current_user(user)


def voter_dashboard():
    _portal.run()
