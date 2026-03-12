import datetime
import hashlib
import random
import string
import json
import os
import time
import sys
from storage import *

if sys.platform == "win32":
    os.system("")

def generate_voter_card_number():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def log_action(action, user, details):
    audit_log.append({"timestamp": str(datetime.datetime.now()), "action": action, "user": user, "details": details})
