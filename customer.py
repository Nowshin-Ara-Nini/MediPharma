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

from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from db import DB

customer_bp = Blueprint("customer", __name__)

# Booking form
@customer_bp.get("/book_appointment")
def book_appointment():
    # Only allow customers
    if session.get("role") != "customer":
        return redirect(url_for("auth.login_page"))
    with DB() as cur:
        cur.execute("SELECT user_id, doctor_name, specialty FROM doctors")
        doctors = cur.fetchall()
    return render_template("book_appointment.html", doctors=doctors)

# Submit booking
@customer_bp.post("/book_appointment")
def book_appointment_submit():
    doctor_id = request.form.get("doctor_id")
    scheduled_at = request.form.get("scheduled_at")
    if not (doctor_id and scheduled_at):
        flash("Doctor and time are required", "error")
        return redirect(url_for("customer.book_appointment"))

    with DB() as cur:
        cur.execute("""
            INSERT INTO appointments (customer_id, doctor_id, scheduled_at)
            VALUES (%s, %s, %s)
        """, (session["uid"], doctor_id, scheduled_at))
    flash("Appointment booked successfully", "success")
    return redirect(url_for("customer.customer_dashboard"))