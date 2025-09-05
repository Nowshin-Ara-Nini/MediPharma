from flask import Blueprint, render_template, session, redirect, url_for, flash
from db import DB

admin_bp = Blueprint("admin", __name__)

# Admin Dashboard
@admin_bp.get("/admin_dashboard")
def admin_dashboard():
    # Ensure the current user is an admin
    if session.get("role") != "admin":
        flash("You must be an admin to access this page", "error")
        return redirect(url_for("auth.login_page"))
    
    return render_template("admin_dashboard.html")

# Manage Users (Example: Block/Change Roles)
@admin_bp.get("/admin/manage_users")
def manage_users():
    with DB() as cur:
        cur.execute("SELECT * FROM users")
        users = cur.fetchall()
    return render_template("manage_users.html", users=users)

# Block or Change Role of User (Example: Block User)
@admin_bp.post("/admin/manage_users/<int:user_id>/block")
def block_user(user_id):
    # Ensure the current user is an admin
    if session.get("role") != "admin":
        flash("You must be an admin to perform this action", "error")
        return redirect(url_for("auth.login_page"))

    # Block the user (update user status to 'blocked' in the database)
    with DB() as cur:
        cur.execute("UPDATE users SET status='blocked' WHERE user_id=%s", (user_id,))
        flash("User has been blocked successfully", "success")
    
    return redirect(url_for("admin.manage_users"))

# Change User Role
@admin_bp.post("/admin/manage_users/<int:user_id>/change_role")
def change_user_role(user_id):
    new_role = request.form.get("role")
    if not new_role:
        flash("Role is required", "error")
        return redirect(url_for("admin.manage_users"))
    
    with DB() as cur:
        cur.execute("UPDATE users SET role=%s WHERE user_id=%s", (new_role, user_id))
        flash(f"User role has been changed to {new_role}", "success")
    
    return redirect(url_for("admin.manage_users"))

