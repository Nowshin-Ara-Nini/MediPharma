from flask import Blueprint, render_template, session, redirect, url_for, flash, request
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
    if session.get("role") != "pharmacist":
        return redirect(url_for("auth.login_page"))

    with DB() as cur:
        cur.execute("""
            SELECT
                m.medicine_id,
                m.name,
                m.description,
                m.price,
                m.production_date,
                m.expiry_date,
                COALESCE(SUM(ii.stock_quantity), 0) AS stock
            FROM inventories i
            JOIN inventory_items ii ON ii.inventory_id = i.inventory_id
            JOIN medicines m        ON m.medicine_id = ii.medicine_id
            WHERE i.pharmacist_id = %s
            GROUP BY m.medicine_id, m.name, m.description, m.price, m.production_date, m.expiry_date
            ORDER BY m.name
        """, (session["uid"],))
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

@pharmacist_bp.route("/request_stock", methods=["POST"])
def request_stock():
    if session.get("role") != "pharmacist":
        return redirect(url_for("auth.login_page"))

    pharmacist_id = session["uid"]
    company_id  = request.form.get("company_id", type=int)
    medicine_id = request.form.get("medicine_id", type=int)
    quantity    = request.form.get("quantity", type=int)

    if not (company_id and medicine_id and quantity):
        flash("Missing request data.", "error")
        return redirect(url_for("pharmacist.pharmacist_medicines"))

    if quantity < 50:
        flash("Minimum request quantity is 50.", "error")
        return redirect(url_for("pharmacist.pharmacist_medicines"))

    from db import DB
    with DB() as cur:
        cur.execute("""
            INSERT INTO stock_requests (pharmacist_id, company_id, medicine_id, quantity, status)
            VALUES (%s, %s, %s, %s, 'pending')
        """, (pharmacist_id, company_id, medicine_id, quantity))

    flash("Stock request sent to the company.", "success")
    return redirect(url_for("pharmacist.pharmacist_medicines"))
