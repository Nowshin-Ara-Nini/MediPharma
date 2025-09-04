from flask import Blueprint, request, redirect, url_for, flash
from db import DB
from utils import current_user_id

feedback_bp = Blueprint("feedback", __name__)

@feedback_bp.post("/feedback")
def leave_feedback():
    uid = current_user_id()
    if not uid:
        flash("Login required", "error"); return redirect(url_for("auth.login_page"))
    medicine_id = int(request.form["medicine_id"]) ; rating = int(request.form["rating"]) ; comments = request.form.get("comments")
    if not (1 <= rating <= 5):
        flash("Rating must be 1-5", "error"); return redirect(url_for("shop.medicines"))
    with DB() as cur:
        # upsert-like via unique constraint (customer_id, medicine_id)
        cur.execute("SELECT feedback_id FROM feedbacks WHERE customer_id=%s AND medicine_id=%s", (uid, medicine_id))
        row = cur.fetchone()
        if row:
            cur.execute("UPDATE feedbacks SET rating=%s, comments=%s, verifiedlogin_flag=1 WHERE feedback_id=%s", (rating, comments, row["feedback_id"]))
        else:
            cur.execute(
                "INSERT INTO feedbacks(customer_id, medicine_id, rating, comments, verifiedlogin_flag) VALUES(%s,%s,%s,%s,1)",
                (uid, medicine_id, rating, comments)
            )
    flash("Feedback saved", "success")
    return redirect(url_for("shop.medicines"))