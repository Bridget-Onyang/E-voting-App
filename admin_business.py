from admin_dashboard import AdminDashboard


_dashboard = AdminDashboard()


def set_current_user(user):
    _dashboard.set_current_user(user)


def admin_dashboard():
    _dashboard.run()
