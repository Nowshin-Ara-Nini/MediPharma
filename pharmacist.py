from flask import Blueprint, render_template, session, redirect, url_for
from db import DB

pharmacist_bp = Blueprint("pharmacist", __name__)

@pharmacist_bp.get("/pharmacist_dashboard")
def pharmacist_dashboard():
    if session.get("role") != "pharmacist":
        return redirect(url_for("auth.login_page"))
    
    return render_template("pharmacist_dashboard.html")

# Pharmacist Profile
@pharmacist_bp.get("/pharmacist_profile")
def pharmacist_profile():
    with DB() as cur:
        cur.execute("SELECT * FROM pharmacists WHERE user_id=%s", (session["uid"],))
        profile = cur.fetchone()
    return render_template("pharmacist_profile.html", profile=profile)

# Pharmacist Orders
@pharmacist_bp.get("/pharmacist_orders")
def pharmacist_orders():
    with DB() as cur:
        cur.execute("SELECT * FROM orders WHERE pharmacist_id=%s", (session["uid"],))
        orders = cur.fetchall()
    return render_template("pharmacist_orders.html", orders=orders)

# Pharmacist Medicines
@pharmacist_bp.get("/pharmacist_medicines")
def pharmacist_medicines():
    with DB() as cur:
        cur.execute("SELECT * FROM medicines WHERE pharmacist_id=%s", (session["uid"],))
        medicines = cur.fetchall()
    return render_template("pharmacist_medicines.html", medicines=medicines)

# Pharmacist Notifications
@pharmacist_bp.get("/pharmacist_notifications")
def notifications():
    if session.get("role") != "pharmacist":
        return redirect(url_for("auth.login_page"))
    with DB() as cur:
        cur.execute("SELECT * FROM notifications WHERE pharmacist_id=%s", (session["uid"],))
        notifications = cur.fetchall()
    return render_template("pharmacist_notifications.html", notifications=notifications)

# Refund Policy
@pharmacist_bp.get("/pharmacist_refund_policy")
def refund_policy():
    if session.get("role") != "pharmacist":
        return redirect(url_for("auth.login_page"))
    return render_template("refund_policy.html")
