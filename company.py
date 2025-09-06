from flask import Blueprint, render_template, session, redirect, url_for
from db import DB

company_bp = Blueprint("company", __name__)

@company_bp.get("/company_dashboard")
def company_dashboard():
    if session.get("role") != "company":
        return redirect(url_for("auth.login_page"))
    
    return render_template("company_dashboard.html")

# Company Profile
@company_bp.get("/company_profile")
def company_profile():
    with DB() as cur:
        cur.execute("SELECT * FROM companies WHERE user_id=%s", (session["uid"],))
        profile = cur.fetchone()
    return render_template("company_profile.html", profile=profile)

# Company Medicines
@company_bp.get("/company_medicines")
def company_medicines():
    with DB() as cur:
        cur.execute("SELECT * FROM medicines WHERE company_id=%s", (session["uid"],))
        medicines = cur.fetchall()
    return render_template("company_medicines.html", medicines=medicines)

# Company Orders
@company_bp.get("/company_orders")
def company_orders():
    with DB() as cur:
        cur.execute("SELECT * FROM orders WHERE company_id=%s", (session["uid"],))
        orders = cur.fetchall()
    return render_template("company_orders.html", orders=orders)
