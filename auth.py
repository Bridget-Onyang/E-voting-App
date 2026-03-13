from auth_service import AuthService


_auth_service = AuthService()


def login():
    return _auth_service.login()


def register_voter():
    return _auth_service.register_voter()
