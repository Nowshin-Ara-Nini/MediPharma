# feedback.py
from flask import Blueprint, request, flash, redirect, url_for
from db import DB
from utils import current_user_id

feedback_bp = Blueprint("feedback", __name__)

@feedback_bp.post("/feedback")
def leave_feedback():
    uid = current_user_id()
    if not uid:
        flash("Login required", "error")
        return redirect(url_for("auth.login_page"))
    
    medicine_id = int(request.form["medicine_id"])
    rating = int(request.form["rating"])
    comments = request.form.get("comments")
    
    if not (1 <= rating <= 5):
        flash("Rating must be 1-5", "error")
        return redirect(url_for("shop.medicines"))
    
    with DB() as cur:
        # Upsert feedback
        cur.execute("SELECT feedback_id FROM feedbacks WHERE customer_id=%s AND medicine_id=%s", (uid, medicine_id))
        row = cur.fetchone()
        if row:
            cur.execute("UPDATE feedbacks SET rating=%s, comments=%s WHERE feedback_id=%s", (rating, comments, row["feedback_id"]))
        else:
            cur.execute("INSERT INTO feedbacks(customer_id, medicine_id, rating, comments) VALUES(%s, %s, %s, %s)", (uid, medicine_id, rating, comments))
    
    flash("Feedback saved", "success")
    return redirect(url_for("shop.medicines"))
# In your Flask app (app.py or wherever routes are defined)
