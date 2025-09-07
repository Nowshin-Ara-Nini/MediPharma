from flask import Blueprint, render_template, session, redirect, url_for
from db import DB

pharmacist_bp = Blueprint("pharmacist", __name__)

@pharmacist_bp.get("/pharmacist_dashboard")
def pharmacist_dashboard():
    if session.get("role") != "pharmacist":
        return redirect(url_for("auth.login_page"))
    return render_template("pharmacist_dashboard.html")

@pharmacist_bp.get("/pharmacist_profile")
def pharmacist_profile():
    with DB() as cur:
        cur.execute("SELECT * FROM pharmacists WHERE user_id=%s", (session["uid"],))
        profile = cur.fetchone()
    return render_template("pharmacist_profile.html", profile=profile)

@pharmacist_bp.get("/pharmacist_medicines")
def pharmacist_medicines():
    with DB() as cur:
        cur.execute("""
            SELECT m.*, ii.stock_quantity
            FROM medicines m
            JOIN inventory_items ii ON ii.medicine_id = m.medicine_id
            JOIN inventories i ON i.inventory_id = ii.inventory_id
            WHERE i.pharmacist_id = %s
        """, (session["uid"],))  # session["uid"] is the pharmacist's ID
        
        medicines = cur.fetchall()
    
    return render_template("pharmacist_medicines.html", medicines=medicines)

@pharmacist_bp.get("/pharmacist_orders")
def pharmacist_orders():
    with DB() as cur:
        cur.execute("SELECT * FROM orders WHERE pharmacist_id=%s", (session["uid"],))
        orders = cur.fetchall()
    return render_template("pharmacist_orders.html", orders=orders)

@pharmacist_bp.get("/pharmacist_notifications", endpoint="notifications")
def pharmacist_notifications():
    with DB() as cur:
        cur.execute("SELECT * FROM notifications WHERE pharmacist_id=%s", (session["uid"],))
        notifications = cur.fetchall()
    return render_template("notifications.html", notifications=notifications)

@pharmacist_bp.get("/pharmacist_refund_policy", endpoint="refund_policy")
def pharmacist_refund_policy():
    if session.get("role") != "pharmacist":
        return redirect(url_for("auth.login_page"))
    return render_template("refund_policy.html")
