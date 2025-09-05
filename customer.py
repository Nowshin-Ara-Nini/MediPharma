from flask import Blueprint, render_template, session, redirect, url_for
from db import DB

customer_bp = Blueprint("customer", __name__)

# Customer Dashboard
@customer_bp.get("/customer_dashboard")
def customer_dashboard():
    # Ensure the current user is a customer
    if session.get("role") != "customer":
        return redirect(url_for("auth.login_page"))
    
    return render_template("customer_dashboard.html")

# Customer Profile
@customer_bp.get("/customer_profile")
def customer_profile():
    with DB() as cur:
        cur.execute("SELECT * FROM customer WHERE user_id=%s", (session["uid"],))
        profile = cur.fetchone()
    return render_template("customer_profile.html", profile=profile)
