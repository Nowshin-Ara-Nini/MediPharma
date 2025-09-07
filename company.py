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
@company_bp.get("/company_medicines")
def company_medicines():
    with DB() as cur:
        cur.execute("""
            SELECT m.*
            FROM medicines m
            JOIN company_manufactures cm ON cm.medicine_id = m.medicine_id
            WHERE cm.company_id = %s
        """, (session["uid"],))  # Filtering by company_id to show only the company's medicines
        
        medicines = cur.fetchall()

    return render_template("company_medicines.html", medicines=medicines)

@company_bp.post("/add_medicine")
def add_medicine():
    name = request.form.get("name")
    description = request.form.get("description")
    price = request.form.get("price")
    production_date = request.form.get("production_date")
    expiry_date = request.form.get("expiry_date")
    
    if not name or not description or not price or not production_date or not expiry_date:
        flash("All fields are required", "error")
        return redirect(url_for("company.company_medicines"))
    
    # Insert the new medicine into the medicines table
    with DB() as cur:
        # Insert the medicine into the `medicines` table with the `company_id`
        cur.execute(
            "INSERT INTO medicines (name, description, price, production_date, expiry_date, company_id) VALUES (%s, %s, %s, %s, %s, %s)",
            (name, description, price, production_date, expiry_date, session["uid"])  # session["uid"] is the company ID
        )
        
        # Fetch the last inserted medicine_id
        medicine_id = cur.lastrowid

        # Now, let's add this medicine to the inventory_items table for the pharmacist
        # Assume that each pharmacist should get a default inventory with 0 stock initially
        # Fetch the pharmacist_id from session (make sure the session contains a valid pharmacist_id)
        pharmacist_id = session.get("uid")  # Assuming `session["uid"]` holds the pharmacist's ID

        # Check if the pharmacist exists in the `pharmacists` table
        cur.execute("SELECT user_id FROM pharmacists WHERE user_id=%s", (pharmacist_id,))
        pharmacist = cur.fetchone()

        if not pharmacist:
            flash("Pharmacist not found", "error")
            return redirect(url_for("company.company_medicines"))
        
        # Check if the pharmacist has an inventory, if not, create one
        cur.execute("SELECT inventory_id FROM inventories WHERE pharmacist_id=%s", (pharmacist_id,))
        inventory = cur.fetchone()

        if not inventory:
            # Create an inventory if it doesn't exist
            cur.execute("INSERT INTO inventories (pharmacist_id, company_id) VALUES (%s, %s)", (pharmacist_id, session["uid"]))
            inventory_id = cur.lastrowid
        else:
            inventory_id = inventory["inventory_id"]

        # Add medicine to the inventory_items table (with stock quantity set to 0 initially)
        cur.execute(
            "INSERT INTO inventory_items (inventory_id, medicine_id, stock_quantity) VALUES (%s, %s, %s)",
            (inventory_id, medicine_id, 0)  # Initially, the stock quantity is set to 0
        )
    
    flash("Medicine added successfully", "success")
    return redirect(url_for("company.company_medicines"))

@company_bp.get("/company_orders")
def company_orders():
    with DB() as cur:
        cur.execute("SELECT * FROM orders WHERE company_id=%s", (session["uid"],))
        orders = cur.fetchall()
    return render_template("company_orders.html", orders=orders)

@company_bp.get("/company_notifications")
def company_notifications():
    with DB() as cur:
        cur.execute("SELECT * FROM notifications WHERE company_id=%s", (session["uid"],))
        notifications = cur.fetchall()
    return render_template("company_notifications.html", notifications=notifications)
