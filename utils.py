from datetime import date, timedelta
from flask import session

EXPIRY_SOON_DAYS = 30

ROLE_TABLES = {
    "customer": "customer",
    "pharmacist": "pharmacists",
    "company": "companies",
    "doctor": "doctors",
    "admin": "admins",
}

def current_user_role():
    return session.get("role")

def current_user_id():
    return session.get("uid")
