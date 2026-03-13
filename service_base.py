class UserBoundService:
    def __init__(self, current_user=None):
        self.current_user = current_user

    def set_current_user(self, user):
        self.current_user = user
