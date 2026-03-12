import time
from ui import *
from utils import *
from storage import *
import auth             # We use the module name to access its variables
import admin_business
import voter_business

### main app
def main():
    print(f"\n  {THEME_LOGIN}Loading E-Voting System...{RESET}")
    load_data()
    time.sleep(1)
    
    while True:
        clear_screen()
        
        # 1. Run the login from the auth module
        logged_in = auth.login()
        
        if logged_in:
            # 2. SYNC: Fetch the user and role from the auth module
            # and push them into the business modules
            user = auth.current_user
            role = auth.current_role
            
            admin_business.current_user = user
            voter_business.current_user = user
            
            # 3. Check the role from the auth module to decide which dashboard to open
            if role == "admin": 
                admin_business.admin_dashboard()
            elif role == "voter": 
                voter_business.voter_dashboard()
            
            # 4. Clean up after logout
            admin_business.current_user = None
            voter_business.current_user = None
            auth.current_user = None
            auth.current_role = None

if __name__ == "__main__":
    main()