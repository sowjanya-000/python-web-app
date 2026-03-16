import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-change-in-production")

# ── Database ──────────────────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///taskflow.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# ── Models ────────────────────────────────────────────────────────────────────
class User(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email    = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created  = db.Column(db.DateTime, default=datetime.utcnow)
    tasks    = db.relationship("Task", backref="owner", lazy=True, cascade="all, delete-orphan")

class Task(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    priority    = db.Column(db.String(10), default="medium")   # low / medium / high
    status      = db.Column(db.String(10), default="todo")     # todo / doing / done
    created     = db.Column(db.DateTime, default=datetime.utcnow)
    user_id     = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

# ── Auth helpers ──────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

def current_user():
    return User.query.get(session["user_id"]) if "user_id" in session else None

# ── Page routes ───────────────────────────────────────────────────────────────
@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("index"))
    return render_template("dashboard.html", user=current_user())

# ── Auth API ──────────────────────────────────────────────────────────────────
@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data or not all(k in data for k in ["username", "email", "password"]):
        return jsonify({"error": "Missing fields"}), 400
    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email already registered"}), 409
    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"error": "Username taken"}), 409
    hashed = bcrypt.generate_password_hash(data["password"]).decode("utf-8")
    user = User(username=data["username"], email=data["email"], password=hashed)
    db.session.add(user)
    db.session.commit()
    session["user_id"] = user.id
    return jsonify({"message": "Registered", "username": user.username}), 201

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing fields"}), 400
    user = User.query.filter_by(email=data.get("email")).first()
    if not user or not bcrypt.check_password_hash(user.password, data.get("password", "")):
        return jsonify({"error": "Invalid credentials"}), 401
    session["user_id"] = user.id
    return jsonify({"message": "Logged in", "username": user.username})

@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})

@app.route("/api/me")
@login_required
def me():
    u = current_user()
    return jsonify({"id": u.id, "username": u.username, "email": u.email})

# ── Tasks API ─────────────────────────────────────────────────────────────────
@app.route("/api/tasks", methods=["GET"])
@login_required
def get_tasks():
    tasks = Task.query.filter_by(user_id=session["user_id"]).order_by(Task.created.desc()).all()
    return jsonify([{
        "id": t.id, "title": t.title, "description": t.description,
        "priority": t.priority, "status": t.status,
        "created": t.created.strftime("%b %d, %Y")
    } for t in tasks])

@app.route("/api/tasks", methods=["POST"])
@login_required
def create_task():
    data = request.get_json()
    if not data or not data.get("title"):
        return jsonify({"error": "Title required"}), 400
    task = Task(
        title=data["title"],
        description=data.get("description", ""),
        priority=data.get("priority", "medium"),
        status=data.get("status", "todo"),
        user_id=session["user_id"]
    )
    db.session.add(task)
    db.session.commit()
    return jsonify({"id": task.id, "title": task.title, "priority": task.priority,
                    "status": task.status, "description": task.description,
                    "created": task.created.strftime("%b %d, %Y")}), 201

@app.route("/api/tasks/<int:task_id>", methods=["PATCH"])
@login_required
def update_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=session["user_id"]).first_or_404()
    data = request.get_json()
    for field in ["title", "description", "priority", "status"]:
        if field in data:
            setattr(task, field, data[field])
    db.session.commit()
    return jsonify({"message": "Updated"})

@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
@login_required
def delete_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=session["user_id"]).first_or_404()
    db.session.delete(task)
    db.session.commit()
    return jsonify({"message": "Deleted"})

@app.route("/api/stats")
@login_required
def stats():
    tasks = Task.query.filter_by(user_id=session["user_id"]).all()
    return jsonify({
        "total": len(tasks),
        "todo":  sum(1 for t in tasks if t.status == "todo"),
        "doing": sum(1 for t in tasks if t.status == "doing"),
        "done":  sum(1 for t in tasks if t.status == "done"),
        "high":  sum(1 for t in tasks if t.priority == "high"),
    })

@app.route("/health")
def health():
    return jsonify({"status": "healthy"})

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8000)), debug=False)
