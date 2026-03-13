import datetime
import hashlib
import random
import string

import storage


VOTER_CARD_LENGTH = 12


def generate_voter_card_number():
    population = string.ascii_uppercase + string.digits
    return "".join(random.choices(population, k=VOTER_CARD_LENGTH))


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def log_action(action, user, details):
    storage.audit_log.append(
        {
            "timestamp": str(datetime.datetime.now()),
            "action": action,
            "user": user,
            "details": details,
        }
    )
