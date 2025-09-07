from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from db import DB

company_bp = Blueprint("company", __name__)

@company_bp.get("/company_dashboard")
def company_dashboard():
    if session.get("role") != "company":
        return redirect(url_for("auth.login_page"))
    return render_template("company_dashboard.html")

@company_bp.get("/company_profile")
def company_profile():
    with DB() as cur:
        cur.execute("SELECT * FROM companies WHERE user_id=%s", (session["uid"],))
        profile = cur.fetchone()
    return render_template("company_profile.html", profile=profile)

# Keep only this version of company_medicines
# company.py
@company_bp.get("/company_medicines")
def company_medicines():
    if session.get("role") != "company":
        return redirect(url_for("auth.login_page"))

    company_id = session["uid"]

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
            LEFT JOIN inventory_items ii ON ii.inventory_id = i.inventory_id
            LEFT JOIN medicines m ON m.medicine_id = ii.medicine_id
            WHERE i.company_id = %s
            GROUP BY m.medicine_id, m.name, m.description, m.price, m.production_date, m.expiry_date
            ORDER BY m.name
        """, (company_id,))
        medicines = cur.fetchall()

    return render_template("company_medicines.html", medicines=medicines)

@company_bp.post("/add_medicine")
def add_medicine():
    name = request.form.get("name")
    description = request.form.get("description")
    price = request.form.get("price")
    production_date = request.form.get("production_date")
    expiry_date = request.form.get("expiry_date")

    if not all([name, description, price, production_date, expiry_date]):
        flash("All fields are required", "error")
        return redirect(url_for("company.company_medicines"))

    company_id = session["uid"]  # logged-in company

    with DB() as cur:
        # 1) Insert medicine (schema has no company_id column)
        cur.execute(
            "INSERT INTO medicines (name, description, price, production_date, expiry_date) "
            "VALUES (%s, %s, %s, %s, %s)",
            (name, description, price, production_date, expiry_date)
        )
        medicine_id = cur.lastrowid

        # 2) Link company ↔ medicine
        cur.execute(
            "INSERT INTO company_manufactures (company_id, medicine_id) VALUES (%s, %s)",
            (company_id, medicine_id)
        )

        # 3) Ensure a company-owned inventory exists (no pharmacist yet)
        cur.execute(
            "SELECT inventory_id FROM inventories "
            "WHERE company_id=%s AND pharmacist_id IS NULL",
            (company_id,)
        )
        row = cur.fetchone()
        if row:
            inventory_id = row["inventory_id"]
        else:
            cur.execute(
                "INSERT INTO inventories (company_id, pharmacist_id) VALUES (%s, NULL)",
                (company_id,)
            )
            inventory_id = cur.lastrowid

        # 4) Add an inventory item with 0 stock (idempotent)
        cur.execute(
            "INSERT INTO inventory_items (inventory_id, medicine_id, stock_quantity) "
            "VALUES (%s, %s, %s) "
            "ON DUPLICATE KEY UPDATE stock_quantity=stock_quantity",
            (inventory_id, medicine_id, 0)
        )

    flash("Medicine added to company inventory.", "success")
    return redirect(url_for("company.company_medicines"))

# company.py
from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from db import DB

@company_bp.get("/company_orders")
def company_orders():
    if session.get("role") != "company":
        return redirect(url_for("auth.login_page"))

    with DB() as cur:
        cur.execute("""
            SELECT
                sr.pharmacist_id,
                up.name AS pharmacist_name,
                sr.medicine_id,
                m.name  AS medicine_name,
                sr.quantity,
                sr.status
            FROM stock_requests sr
            JOIN users up         ON up.user_id = sr.pharmacist_id
            LEFT JOIN medicines m ON m.medicine_id = sr.medicine_id
            WHERE sr.company_id = %s
            ORDER BY FIELD(sr.status,'pending','approved','rejected','fulfilled'),
                     m.name, up.name
        """, (session["uid"],))
        orders = cur.fetchall()

    return render_template("company_orders.html", orders=orders)
@company_bp.get("/company_notifications", endpoint="notifications")
def company_notifications():
    with DB() as cur:
        cur.execute("SELECT * FROM notifications WHERE company_id=%s", (session["uid"],))
        notifications = cur.fetchall()
    return render_template("company_notifications.html", notifications=notifications)

@company_bp.get("/company_refund_policy", endpoint="refund_policy")
def company_refund_policy():
    if session.get("role") != "company":
        return redirect(url_for("auth.login_page"))
    return render_template("refund_policy.html")

@company_bp.post("/company_orders/fulfill")
def fulfill_order():
    if session.get("role") != "company":
        return redirect(url_for("auth.login_page"))

    company_id    = session["uid"]
    pharmacist_id = request.form.get("pharmacist_id", type=int)
    medicine_id   = request.form.get("medicine_id", type=int)
    quantity      = request.form.get("quantity", type=int)

    if not (pharmacist_id and medicine_id and quantity):
        flash("Missing data to fulfill.", "error")
        return redirect(url_for("company.company_orders"))

    with DB() as cur:
        # Ensure a pharmacist-specific inventory exists for this company
        cur.execute("""
            SELECT inventory_id
            FROM inventories
            WHERE company_id=%s AND pharmacist_id=%s
        """, (company_id, pharmacist_id))
        row = cur.fetchone()
        if row:
            inv_ph_id = row["inventory_id"]
        else:
            cur.execute("""
                INSERT INTO inventories(company_id, pharmacist_id)
                VALUES(%s, %s)
            """, (company_id, pharmacist_id))
            inv_ph_id = cur.lastrowid

        # Upsert the quantity INTO the pharmacist's inventory
        cur.execute("""
            INSERT INTO inventory_items(inventory_id, medicine_id, stock_quantity)
            VALUES(%s, %s, %s)
            ON DUPLICATE KEY UPDATE stock_quantity = stock_quantity + VALUES(stock_quantity)
        """, (inv_ph_id, medicine_id, quantity))

        # Mark one matching pending request as fulfilled
        cur.execute("""
            UPDATE stock_requests
            SET status='fulfilled'
            WHERE company_id=%s AND pharmacist_id=%s AND medicine_id=%s AND status='pending'
            LIMIT 1
        """, (company_id, pharmacist_id, medicine_id))

    flash("Request fulfilled and stock stored in pharmacist inventory.", "success")
    return redirect(url_for("company.company_orders"))