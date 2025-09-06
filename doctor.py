from flask import Blueprint, render_template, session, redirect, url_for
from db import DB

doctor_bp = Blueprint("doctor", __name__)

# Doctor Dashboard
@doctor_bp.get("/doctor_dashboard")
def doctor_dashboard():
    # Ensure the current user is a doctor
    if session.get("role") != "doctor":
        return redirect(url_for("auth.login_page"))
    
    return render_template("doctor_dashboard.html")

# Doctor Appointments
@doctor_bp.get("/doctor_appointments")
def doctor_appointments():
    with DB() as cur:
        cur.execute("SELECT * FROM appointments WHERE user_id=%s", (session["uid"],))
        appointments = cur.fetchall()
    return render_template("doctor_appointments.html", appointments=appointments)

# Doctor Notes (viewing important notes about patients)
@doctor_bp.get("/doctor_notes")
def doctor_notes():
    with DB() as cur:
        cur.execute("SELECT * FROM notes WHERE user_id=%s", (session["uid"],))
        notes = cur.fetchall()
    return render_template("doctor_notes.html", notes=notes)

# Doctor Profile
@doctor_bp.get("/doctor_profile")
def doctor_profile():
    # Ensure the current user is a doctor
    if session.get("role") != "doctor":
        return redirect(url_for("auth.login_page"))
    with DB() as cur:
        cur.execute("SELECT * FROM doctors WHERE user_id=%s", (session["uid"],))
        doctor = cur.fetchone()
    return render_template("doctor_profile.html", doctor=doctor)

# Doctor Notifications
@doctor_bp.get("/doctor_notifications")
def notifications():
    # Ensure the current user is a doctor
    if session.get("role") != "doctor":
        return redirect(url_for("auth.login_page"))
    with DB() as cur:
        cur.execute("SELECT * FROM notifications WHERE user_id=%s", (session["uid"],))
        notifications = cur.fetchall()
    return render_template("notifications.html", notifications=notifications)
