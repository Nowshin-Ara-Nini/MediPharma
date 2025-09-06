from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from db import DB

customer_bp = Blueprint("customer", __name__)

@customer_bp.get("/customer_dashboard")
def customer_dashboard():
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

# Customer Orders
@customer_bp.get("/customer_orders")
def customer_orders():
    with DB() as cur:
        cur.execute("SELECT * FROM orders WHERE customer_id=%s", (session["uid"],))
        orders = cur.fetchall()
    return render_template("customer_orders.html", orders=orders)

# Customer Appointments
@customer_bp.get("/my_appointments")
def my_appointments():
    with DB() as cur:
        cur.execute("""
            SELECT a.appointment_id, a.scheduled_at, d.doctor_name
            FROM appointments a
            JOIN doctors d ON a.doctor_id = d.user_id
            WHERE a.customer_id = %s
            ORDER BY a.scheduled_at DESC
        """, (session["uid"],))
        appointments = cur.fetchall()
    
    return render_template("customer_appointments.html", appointments=appointments)

# Refund and Return Policy
@customer_bp.get("/refund_policy")
def refund_policy():
    return render_template("refund_policy.html")

# Customer Reviews (My Rating and Reviews)
@customer_bp.get("/customer_reviews")
def customer_reviews():
    with DB() as cur:
        cur.execute("""
            SELECT f.feedback_id, m.name AS medicine_name, f.rating, f.comments
            FROM feedbacks f
            JOIN medicines m ON f.medicine_id = m.medicine_id
            WHERE f.customer_id = %s
        """, (session["uid"],))
        reviews = cur.fetchall()
    
    return render_template("customer_reviews.html", reviews=reviews)

# Notifications
@customer_bp.get("/notifications")
def notifications():
    with DB() as cur:
        # Retrieve all notifications for the customer
        cur.execute("""
            SELECT * FROM notifications
            WHERE user_id = %s
            ORDER BY created_at DESC
        """, (session["uid"],))
        notifications = cur.fetchall()
    
    return render_template("notifications.html", notifications=notifications)


# List Doctors and Book Appointment
@customer_bp.get("/list_doctors")
def list_doctors():
    if session.get("role") != "customer":
        return redirect(url_for("auth.login_page"))

    # Fetch all doctors from the database
    with DB() as cur:
        cur.execute("SELECT * FROM doctors")
        doctors = cur.fetchall()

    return render_template("list_doctors.html", doctors=doctors)

# Book Appointment with Doctor
@customer_bp.post("/book_appointment")
def book_appointment():
    if session.get("role") != "customer":
        return redirect(url_for("auth.login_page"))

    doctor_id = request.form.get("doctor_id")
    scheduled_at = request.form.get("scheduled_at")
    if not doctor_id or not scheduled_at:
        flash("Doctor and time are required", "error")
        return redirect(url_for("customer.list_doctors"))

    with DB() as cur:
        # Insert a new appointment into the appointments table
        cur.execute("""
            INSERT INTO appointments (customer_id, doctor_id, scheduled_at)
            VALUES (%s, %s, %s)
        """, (session["uid"], doctor_id, scheduled_at))

    flash("Appointment booked successfully", "success")
    return redirect(url_for("customer.list_doctors"))

# Cancel Appointment
# @customer_bp.post("/cancel_appointment/<int:appointment_id>")