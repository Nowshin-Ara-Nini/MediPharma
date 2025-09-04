from flask import Flask, render_template, request, session
from auth import auth_bp
from shop import shop_bp
from feedback import feedback_bp

app = Flask(__name__)
app.secret_key = "dev-secret-change-me"

app.register_blueprint(auth_bp)
app.register_blueprint(shop_bp)
app.register_blueprint(feedback_bp)

@app.get("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)