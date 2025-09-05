from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from passlib.hash import bcrypt
from db import DB
from utils import ROLE_TABLES

auth_bp = Blueprint("auth", __name__)

@auth_bp.get("/login")
def login_page():
    return render_template("auth_login.html")

@auth_bp.post("/login")
def login_submit():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    role = request.form.get("role")
    if not (email and password and role):
        flash("All fields are required", "error")
        return redirect(url_for("auth.login_page"))
    with DB() as cur:
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        u = cur.fetchone()
        if not u or not bcrypt.verify(password, u["password_hash"]):
            flash("Invalid credentials", "error")
            return redirect(url_for("auth.login_page"))
        # role check
        table = ROLE_TABLES.get(role)
        if not table:
            flash("Invalid role", "error")
            return redirect(url_for("auth.login_page"))
        cur.execute(f"SELECT 1 FROM {table} WHERE user_id=%s", (u["user_id"],))
        if not cur.fetchone():
            flash("This account does not have selected role.", "error")
            return redirect(url_for("auth.login_page"))
    session["uid"] = u["user_id"]
    session["name"] = u["name"]
    session["role"] = role
    flash("Logged in successfully", "success")
    return redirect(url_for("index"))

@auth_bp.get("/register")
def register_page():
    return render_template("auth_register.html")

@auth_bp.post("/register")
def register_submit():
    name = request.form.get("name"); email = request.form.get("email","\n").strip().lower()
    phone = request.form.get("phone"); address = request.form.get("address")
    role = request.form.get("role"); password = request.form.get("password")
    license_no = request.form.get("license_no")
    education = request.form.get("education")
    speciality = request.form.get("speciality")
    if not (name and email and phone and address and role and password):
        flash("All fields are required", "error"); return redirect(url_for("auth.register_page"))
    pw_hash = bcrypt.hash(password)
    with DB() as cur:
        cur.execute("SELECT 1 FROM users WHERE email=%s", (email,))
        if cur.fetchone():
            flash("Email already registered", "error"); return redirect(url_for("auth.register_page"))
        # Save role in users table
        cur.execute(
            "INSERT INTO users(name, phone, email, address, password_hash, role) VALUES(%s,%s,%s,%s,%s,%s)",
            (name, phone, email, address, pw_hash, role)
        )
        uid = cur.lastrowid
        if role == "customer":
            cur.execute("INSERT INTO customer(user_id, age) VALUES(%s, NULL)", (uid,))
        elif role == "admin":
            cur.execute("INSERT INTO admins(user_id) VALUES(%s)", (uid,))
        elif role == "pharmacist":
            if not license_no:
                flash("License is required for pharmacists", "error"); return redirect(url_for("auth.register_page"))
            cur.execute("INSERT INTO pharmacists(user_id, license_no) VALUES(%s,%s)", (uid, license_no))
        elif role == "company":
            if not license_no:
                flash("License is required for companies", "error"); return redirect(url_for("auth.register_page"))
            cur.execute("INSERT INTO companies(user_id, license_no) VALUES(%s,%s)", (uid, license_no))
        elif role == "doctor":
            if not license_no:
                flash("License is required for doctors", "error"); return redirect(url_for("auth.register_page"))
            if not education or not speciality:
                flash("Education and Speciality are required for doctors", "error"); return redirect(url_for("auth.register_page"))
            cur.execute(
                "INSERT INTO doctors(user_id, doctor_name, license_no, education, contact, specialty) VALUES(%s,%s,%s,%s,%s,%s)",
                (uid, name, license_no, education, phone, speciality)
            )
        else:
            flash("Invalid role", "error"); return redirect(url_for("auth.register_page"))
    flash("Registration successful. Please login.", "success")
    return redirect(url_for("auth.login_page"))

@auth_bp.get("/logout")
def logout():
    session.clear()
    flash("Logged out", "info")
    return redirect(url_for("index"))