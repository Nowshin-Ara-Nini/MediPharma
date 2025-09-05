from flask import Blueprint, render_template, session, redirect, url_for
from db import DB

pharmacist_bp = Blueprint("pharmacist", __name__)

# Pharmacist Dashboard
@pharmacist_bp.get("/pharmacist_dashboard")
def pharmacist_dashboard():
    # Ensure the current user is a pharmacist
    if session.get("role") != "pharmacist":
        return redirect(url_for("auth.login_page"))
    
    return render_template("pharmacist_dashboard.html")

# Pharmacist Medicines (viewing medicines they are selling)
@pharmacist_bp.get("/pharmacist_medicines")
def pharmacist_medicines():
    with DB() as cur:
        cur.execute("SELECT * FROM medicines WHERE pharmacist_id=%s", (session["uid"],))
        medicines = cur.fetchall()
    return render_template("pharmacist_medicines.html", medicines=medicines)
