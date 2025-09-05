from flask import Flask, render_template, request, session, redirect, url_for, flash
from auth import auth_bp
from shop import shop_bp
from feedback import feedback_bp
from admin import admin_bp  # Import the admin blueprint
from customer import customer_bp  # Import the customer blueprint
from pharmacist import pharmacist_bp  # Import the pharmacist blueprint
from company import company_bp  # Import the company blueprint
from doctor import doctor_bp  # Import the doctor blueprint

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

if __name__ == "__main__":
    app.run(debug=True)

