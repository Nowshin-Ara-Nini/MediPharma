from flask import Flask, render_template, request, session, redirect, url_for, flash
from auth import auth_bp
from shop import shop_bp
from feedback import feedback_bp
from admin import admin_bp  # Import the admin blueprint
from customer import customer_bp  # Import the customer blueprint
from pharmacist import pharmacist_bp  # Import the pharmacist blueprint
from company import company_bp  # Import the company blueprint
from doctor import doctor_bp  # Import the doctor blueprint
from db import DB

app = Flask(__name__)
app.secret_key = "dev-secret-change-me"

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(shop_bp)
app.register_blueprint(feedback_bp)
app.register_blueprint(admin_bp)  # Register the admin blueprint
app.register_blueprint(customer_bp)  # Register the customer blueprint
app.register_blueprint(pharmacist_bp)  # Register the pharmacist blueprint
app.register_blueprint(company_bp)  # Register the company blueprint
app.register_blueprint(doctor_bp)  # Register the doctor blueprint

@app.get("/")
def index():
    return render_template("index.html")

# Route to handle the dashboard redirect based on the user's role
@app.route("/dashboard")
def dashboard():
    role = session.get("role")
    
    # Check user's role and redirect to the appropriate dashboard
    if role == "admin":
        return redirect(url_for("admin.admin_dashboard"))
    elif role == "customer":
        return redirect(url_for("customer.customer_dashboard"))
    elif role == "pharmacist":
        return redirect(url_for("pharmacist.pharmacist_dashboard"))
    elif role == "company":
        return redirect(url_for("company.company_dashboard"))
    elif role == "doctor":
        return redirect(url_for("doctor.doctor_dashboard"))
    else:
        flash("Unauthorized access", "error")
        return redirect(url_for("auth.login_page"))
# Route to handle feedback submission (POST request)
# Route for Feedback Form (GET request)
# Route to render the feedback form
@app.route("/feedback/<int:medicine_id>", methods=["GET"])
def feedback(medicine_id):
    # Fetch the medicine name or other details (if needed)
    with DB() as cur:
        cur.execute("SELECT name FROM medicines WHERE medicine_id = %s", (medicine_id,))
        medicine = cur.fetchone()

    # Render the feedback form page
    return render_template("feedback_form.html", medicine_id=medicine_id, medicine_name=medicine['name'])
# Route to handle feedback submission (POST request)
@app.route("/feedback/<int:medicine_id>", methods=["POST"])
def submit_feedback(medicine_id):
    rating = request.form.get("rating")
    comments = request.form.get("comments")
    customer_id = session.get("uid")  # Assuming the customer is logged in, get the user ID

    # Ensure the feedback data is valid
    if not (1 <= int(rating) <= 5):
        flash("Please provide a valid rating (1-5).", "error")
        return redirect(url_for("feedback", medicine_id=medicine_id))

    with DB() as cur:
        # Check if feedback already exists for this customer and medicine
        cur.execute("""
            SELECT feedback_id FROM feedbacks 
            WHERE medicine_id = %s AND customer_id = %s
        """, (medicine_id, customer_id))

        existing_feedback = cur.fetchone()

        if existing_feedback:
            # Update existing feedback
            cur.execute("""
                UPDATE feedbacks 
                SET rating = %s, comments = %s
                WHERE feedback_id = %s
            """, (rating, comments, existing_feedback["feedback_id"]))
            flash("Your feedback has been updated!", "success")
        else:
            # Insert new feedback
            cur.execute("""
                INSERT INTO feedbacks (medicine_id, customer_id, rating, comments)
                VALUES (%s, %s, %s, %s)
            """, (medicine_id, customer_id, rating, comments))
            flash("Your feedback has been submitted successfully!", "success")

    return redirect(url_for("shop.medicines"))
# Route to handle feedback submission (POST request)

    # Rest of the code for handling feedback submission
@app.route("/customer_reviews")
def customer_reviews():
    customer_id = session.get("uid")  # Assuming customer is logged in
    
    with DB() as cur:
        cur.execute("""
            SELECT f.rating, f.comments, m.name AS medicine_name
            FROM feedbacks f
            JOIN medicines m ON f.medicine_id = m.medicine_id
            WHERE f.customer_id = %s
        """, (customer_id,))
        reviews = cur.fetchall()

    return render_template("customer_reviews.html", reviews=reviews)




if __name__ == "__main__":
    app.run(debug=True)

