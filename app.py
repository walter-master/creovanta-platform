import os
import sqlite3
import uuid
from collections import defaultdict, deque
from io import BytesIO
from datetime import datetime, timedelta, timezone
from functools import wraps
from threading import Lock
from typing import Any

import jwt
import requests
import stripe
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_file, send_from_directory
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__, template_folder="templates", static_folder="static")
is_production = os.getenv("FLASK_ENV", "").lower() == "production"
secret_key = os.getenv("SECRET_KEY")
if is_production and not secret_key:
    raise RuntimeError("SECRET_KEY must be configured when FLASK_ENV=production.")
app.config["SECRET_KEY"] = secret_key or "local-development-only-secret-32-bytes"
app.config["JWT_ALGORITHM"] = "HS256"
app.config["UPLOAD_FOLDER"] = os.getenv(
    "UPLOAD_FOLDER", os.path.join(os.path.dirname(__file__), "uploads")
)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
app.config["FIREWALL_RATE_LIMIT"] = int(os.getenv("FIREWALL_RATE_LIMIT", "120"))
app.config["FIREWALL_AUTH_RATE_LIMIT"] = int(os.getenv("FIREWALL_AUTH_RATE_LIMIT", "10"))
app.config["TRUST_PROXY_HEADERS"] = os.getenv("TRUST_PROXY_HEADERS", "true").lower() == "true"
app.config["APP_URL"] = os.getenv("APP_URL", "http://localhost:5000")
app.config["STRIPE_SECRET_KEY"] = os.getenv("STRIPE_SECRET_KEY")
app.config["STRIPE_PUBLISHABLE_KEY"] = os.getenv("STRIPE_PUBLISHABLE_KEY")
app.config["STRIPE_WEBHOOK_SECRET"] = os.getenv("STRIPE_WEBHOOK_SECRET")
app.config["REQUIRE_PAID_ACCESS"] = os.getenv("REQUIRE_PAID_ACCESS", "true").lower() == "true"
app.config["STRIPE_TRIAL_DAYS"] = 90
app.config["BILLING_PLANS"] = {
    "pro": {"name": "Pro", "price": 19.00, "description": "For independent engineers and small technical teams."},
    "team": {"name": "Team", "price": 49.00, "description": "For teams coordinating projects, documents, and reviews."},
}
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.getenv("FLASK_ENV") == "production"
app.config["PREFERRED_URL_SCHEME"] = "https"
app.config["PROPAGATE_EXCEPTIONS"] = False
app.config["DATABASE_URL"] = os.getenv("DATABASE_URL")
app.config["SUPABASE_URL"] = os.getenv("SUPABASE_URL")
app.config["SUPABASE_SERVICE_ROLE_KEY"] = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
app.config["SUPABASE_STORAGE_BUCKET"] = os.getenv("SUPABASE_STORAGE_BUCKET", "documents")

bcrypt = Bcrypt(app)
DB_PATH = os.getenv("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "creovanta.db"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
UPLOAD_FOLDER = app.config["UPLOAD_FOLDER"]
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

if app.config["STRIPE_SECRET_KEY"]:
    stripe.api_key = app.config["STRIPE_SECRET_KEY"]

_firewall_hits = defaultdict(deque)
_firewall_lock = Lock()


def get_db():
    if app.config["DATABASE_URL"]:
        return PostgresConnection(app.config["DATABASE_URL"])
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


class PostgresConnection:
    def __init__(self, database_url: str):
        self.connection = psycopg.connect(database_url, row_factory=dict_row)

    def execute(self, query, params=()):
        query = query.replace("?", "%s").replace(
            "INTEGER PRIMARY KEY AUTOINCREMENT", "BIGSERIAL PRIMARY KEY"
        )
        return self.connection.execute(query, params)

    def executemany(self, query, params):
        query = query.replace("?", "%s").replace(
            "INTEGER PRIMARY KEY AUTOINCREMENT", "BIGSERIAL PRIMARY KEY"
        )
        with self.connection.cursor() as cursor:
            cursor.executemany(query, params)
        return cursor

    def commit(self):
        self.connection.commit()

    def close(self):
        self.connection.close()


def supabase_storage_enabled():
    return bool(app.config["SUPABASE_URL"] and app.config["SUPABASE_SERVICE_ROLE_KEY"])


def supabase_storage_headers():
    key = app.config["SUPABASE_SERVICE_ROLE_KEY"]
    return {"Authorization": f"Bearer {key}", "apikey": key}


def upload_to_supabase(path, content, content_type):
    bucket = app.config["SUPABASE_STORAGE_BUCKET"]
    url = f"{app.config['SUPABASE_URL'].rstrip('/')}/storage/v1/object/{bucket}/{path}"
    response = requests.post(
        url,
        headers={**supabase_storage_headers(), "Content-Type": content_type},
        data=content,
        timeout=30,
    )
    response.raise_for_status()


def download_from_supabase(path):
    bucket = app.config["SUPABASE_STORAGE_BUCKET"]
    url = f"{app.config['SUPABASE_URL'].rstrip('/')}/storage/v1/object/{bucket}/{path}"
    response = requests.get(url, headers=supabase_storage_headers(), timeout=30)
    response.raise_for_status()
    return response.content


def init_db():
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'engineer',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            category TEXT,
            status TEXT DEFAULT 'In progress',
            priority TEXT DEFAULT 'Medium',
            progress INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            status TEXT DEFAULT 'Queued',
            owner TEXT DEFAULT 'You',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(project_id) REFERENCES projects(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS milestones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            status TEXT DEFAULT 'Planned',
            progress INTEGER DEFAULT 0,
            due_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(project_id) REFERENCES projects(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            rating REAL DEFAULT 4.8,
            description TEXT,
            stock INTEGER DEFAULT 50,
            image TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            items TEXT NOT NULL,
            total REAL NOT NULL,
            status TEXT DEFAULT 'paid',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            stripe_subscription_id TEXT UNIQUE,
            plan TEXT NOT NULL,
            status TEXT NOT NULL,
            trial_ends_at TEXT,
            current_period_end TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            file_name TEXT NOT NULL,
            original_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            content_type TEXT DEFAULT 'application/octet-stream',
            size INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )
    conn.commit()

    admin_email = "admin@creovanta.io"
    engineer_email = "engineer@creovanta.io"
    reviewer_email = "reviewer@creovanta.io"

    for email, full_name, role, password in [
        (admin_email, "Admin User", "admin", "Admin@123"),
        (engineer_email, "Engineer User", "engineer", "Engineer@123"),
        (reviewer_email, "Reviewer User", "reviewer", "Reviewer@123"),
    ]:
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing is None:
            conn.execute(
                "INSERT INTO users (full_name, email, password_hash, role) VALUES (?, ?, ?, ?)",
                (full_name, email, bcrypt.generate_password_hash(password).decode("utf-8"), role),
            )

    if conn.execute("SELECT id FROM products LIMIT 1").fetchone() is None:
        seed_products = [
            ("PLC Programming Toolkit", "Automation", 49.0, 4.9, "Industrial control logic templates, documentation, and troubleshooting flows.", 45, "🧰"),
            ("Industrial Design Templates", "Design", 39.0, 4.8, "Detailed mechanical and electrical design canvases for engineering teams.", 60, "🛠️"),
            ("AI Workflow Pack", "AI", 59.0, 5.0, "Workflow automations for product reviews, engineering briefs, and test planning.", 80, "🤖"),
            ("Electrical Calculators Bundle", "Systems", 29.0, 4.7, "Useful calculators for loads, cable sizing, and process energy estimates.", 52, "📐"),
            ("Prototype Documentation Kit", "Product", 35.0, 4.9, "A set of technical record templates used to test and ship product iterations.", 32, "📦"),
            ("Engineering CV Pack", "Career", 22.0, 4.8, "Career-ready templates and guidance for engineering applications and interviews.", 137, "📘"),
        ]
        conn.executemany(
            "INSERT INTO products (name, category, price, rating, description, stock, image) VALUES (?, ?, ?, ?, ?, ?, ?)",
            seed_products,
        )

    conn.commit()
    conn.close()


def create_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "exp": now + timedelta(days=7),
        "iat": now,
    }
    return jwt.encode(payload, app.config["SECRET_KEY"], algorithm=app.config["JWT_ALGORITHM"])


def decode_token(token: str):
    try:
        return jwt.decode(token, app.config["SECRET_KEY"], algorithms=[app.config["JWT_ALGORITHM"]])
    except Exception:
        return None


def get_user_by_id(user_id: int):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(user) if user else None


def get_user_by_email(email: str):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email.lower(),)).fetchone()
    conn.close()
    return dict(user) if user else None


def auth_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authentication required."}), 401
        token = auth_header.split(" ", 1)[1]
        payload = decode_token(token)
        if not payload:
            return jsonify({"error": "Invalid or expired token."}), 401
        try:
            user_id = int(payload.get("sub"))
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid token subject."}), 401
        user = get_user_by_id(user_id)
        if not user:
            return jsonify({"error": "User not found."}), 401
        return func(user, *args, **kwargs)

    return wrapper


def admin_required(func):
    @wraps(func)
    def wrapper(user, *args, **kwargs):
        if user.get("role") != "admin":
            return jsonify({"error": "Admin access required."}), 403
        return func(user, *args, **kwargs)

    return wrapper


def has_paid_access(user):
    if user.get("role") == "admin" or not app.config["REQUIRE_PAID_ACCESS"]:
        return True
    conn = get_db()
    subscription = conn.execute(
        "SELECT id FROM subscriptions WHERE user_id = ? AND status IN ('trialing', 'active', 'past_due') "
        "ORDER BY updated_at DESC LIMIT 1",
        (user["id"],),
    ).fetchone()
    if subscription:
        conn.close()
        return True
    order = conn.execute(
        "SELECT id FROM orders WHERE user_id = ? AND status IN ('paid', 'active', 'mock_paid') "
        "ORDER BY created_at DESC LIMIT 1",
        (user["id"],),
    ).fetchone()
    conn.close()
    return bool(order)


def paid_access_required(func):
    @wraps(func)
    def wrapper(user, *args, **kwargs):
        if not has_paid_access(user):
            return jsonify({"error": "A verified payment is required to access the workspace.", "code": "payment_required"}), 402
        return func(user, *args, **kwargs)
    return wrapper


def require_roles(*allowed_roles):
    def decorator(func):
        @wraps(func)
        def wrapper(user, *args, **kwargs):
            if user.get("role") not in allowed_roles:
                return jsonify({"error": "You do not have permission to perform this action."}), 403
            return func(user, *args, **kwargs)

        return wrapper

    return decorator


def serialize_user(user: dict):
    role_permissions = {
        "admin": ["admin", "manage_users", "manage_projects", "manage_store", "manage_documents", "view_reports"],
        "engineer": ["create_projects", "manage_tasks", "upload_documents", "chat_ai", "purchase_store"],
        "reviewer": ["view_reports", "review_projects", "manage_documents", "chat_ai"],
    }
    return {
        "id": user["id"],
        "name": user["full_name"],
        "email": user["email"],
        "role": user["role"],
        "paidAccess": has_paid_access(user),
        "permissions": role_permissions.get(user["role"], []),
        "createdAt": user["created_at"],
    }


def serialize_document(document: dict):
    return {
        "id": document["id"],
        "user_id": document["user_id"],
        "file_name": document["file_name"],
        "original_name": document["original_name"],
        "content_type": document["content_type"],
        "size": document["size"],
        "created_at": document["created_at"],
        "download_url": f"/api/documents/{document['id']}/download",
    }


def project_progress(conn, project_id: int) -> int:
    milestones = conn.execute(
        "SELECT progress FROM milestones WHERE project_id = ?", (project_id,)
    ).fetchall()
    if milestones:
        return round(sum(row["progress"] for row in milestones) / len(milestones))

    tasks = conn.execute(
        "SELECT status FROM tasks WHERE project_id = ?", (project_id,)
    ).fetchall()
    if not tasks:
        return 0

    completed = sum(row["status"].lower() in {"done", "complete", "completed"} for row in tasks)
    return round(completed / len(tasks) * 100)


def serialize_project(conn, project):
    project_data = dict(project)
    project_data["progress"] = project_progress(conn, project["id"])
    project_data["task_count"] = conn.execute(
        "SELECT COUNT(*) AS count FROM tasks WHERE project_id = ?", (project["id"],)
    ).fetchone()["count"]
    project_data["milestone_count"] = conn.execute(
        "SELECT COUNT(*) AS count FROM milestones WHERE project_id = ?", (project["id"],)
    ).fetchone()["count"]
    return project_data


def user_can_access_project(conn, user, project_id):
    project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not project:
        return None
    if user["role"] != "admin" and project["user_id"] != user["id"]:
        return False
    return project


@app.after_request
def set_security_headers(response):
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    if is_production:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return response


def request_client_ip():
    if app.config["TRUST_PROXY_HEADERS"]:
        forwarded = request.headers.get("X-Forwarded-For", "")
        if forwarded:
            return forwarded.split(",", 1)[0].strip()
    return request.remote_addr or "unknown"


@app.before_request
def application_firewall():
    if "\x00" in request.path or ".." in request.path:
        return jsonify({"error": "Request blocked by firewall."}), 400

    limit = app.config["FIREWALL_AUTH_RATE_LIMIT"] if request.path in {
        "/api/auth/login",
        "/api/auth/register",
    } else app.config["FIREWALL_RATE_LIMIT"]
    bucket = f"{request_client_ip()}:{request.path in {'/api/auth/login', '/api/auth/register'}}"
    now = datetime.now(timezone.utc).timestamp()
    with _firewall_lock:
        hits = _firewall_hits[bucket]
        while hits and now - hits[0] >= 60:
            hits.popleft()
        if len(hits) >= limit:
            response = jsonify({"error": "Too many requests. Try again later."})
            response.status_code = 429
            response.headers["Retry-After"] = "60"
            return response
        hits.append(now)


@app.route("/")
def index():
    return render_template("landing.html")


@app.route("/app")
def application():
    return render_template("index.html")


@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    full_name = str(data.get("full_name") or "").strip()
    email = str(data.get("email") or "").strip().lower()
    password = str(data.get("password") or "")

    if not full_name or not email or len(password) < 6:
        return jsonify({"error": "Full name, valid email, and a password of at least 6 characters are required."}), 400

    if get_user_by_email(email):
        return jsonify({"error": "An account already exists for this email."}), 409

    password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO users (full_name, email, password_hash, role) VALUES (?, ?, ?, ?)",
        (full_name, email, password_hash, "engineer"),
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()

    token = create_token(user_id)
    user = get_user_by_id(user_id)
    return jsonify({"token": token, "user": serialize_user(user)})


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email") or "").strip().lower()
    password = str(data.get("password") or "")

    user = get_user_by_email(email)
    if not user or not bcrypt.check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid email or password."}), 401

    token = create_token(user["id"])
    return jsonify({"token": token, "user": serialize_user(user)})


@app.route("/api/auth/me")
@auth_required
def auth_me(user):
    return jsonify({"user": serialize_user(user)})


@app.route("/api/users")
@auth_required
@admin_required
def list_users(user):
    conn = get_db()
    rows = conn.execute("SELECT id, full_name, email, role, created_at FROM users ORDER BY created_at DESC").fetchall()
    conn.close()
    return jsonify({"users": [dict(row) for row in rows]})


@app.route("/api/healthz")
def healthz():
    return jsonify({"status": "ok", "service": "creovanta"})


@app.route("/api/documents")
@auth_required
@paid_access_required
def list_documents(user):
    conn = get_db()
    if user["role"] == "admin":
        rows = conn.execute("SELECT * FROM documents ORDER BY created_at DESC").fetchall()
    else:
        rows = conn.execute("SELECT * FROM documents WHERE user_id = ? ORDER BY created_at DESC", (user["id"],)).fetchall()
    conn.close()
    return jsonify({"documents": [serialize_document(dict(row)) for row in rows]})


@app.route("/api/documents/upload", methods=["POST"])
@auth_required
@paid_access_required
@require_roles("admin", "engineer", "reviewer")
def upload_document(user):
    if "file" not in request.files:
        return jsonify({"error": "No file was provided."}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file."}), 400

    safe_name = secure_filename(file.filename)
    if not safe_name:
        return jsonify({"error": "The uploaded filename is not valid."}), 400

    stored_name = f"{uuid.uuid4().hex}_{safe_name}"
    content = file.read()
    if supabase_storage_enabled():
        file_path = stored_name
        upload_to_supabase(file_path, content, file.mimetype or "application/octet-stream")
        size = len(content)
    else:
        file_path = os.path.join(UPLOAD_FOLDER, stored_name)
        with open(file_path, "wb") as destination:
            destination.write(content)
        size = os.path.getsize(file_path)

    conn = get_db()
    conn.execute(
        "INSERT INTO documents (user_id, file_name, original_name, file_path, content_type, size) VALUES (?, ?, ?, ?, ?, ?)",
        (user["id"], stored_name, safe_name, file_path, file.mimetype or "application/octet-stream", size),
    )
    conn.commit()
    document_id = conn.execute("SELECT id FROM documents WHERE file_name = ? AND user_id = ? ORDER BY id DESC LIMIT 1", (stored_name, user["id"])).fetchone()
    conn.close()

    if not document_id:
        return jsonify({"error": "File was uploaded but metadata could not be saved."}), 500

    return jsonify({"message": "Document uploaded successfully.", "document_id": document_id["id"]})


@app.route("/api/documents/<int:document_id>/download")
@auth_required
@paid_access_required
def download_document(user, document_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM documents WHERE id = ?", (document_id,)).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Document not found."}), 404

    if user["role"] != "admin" and row["user_id"] != user["id"]:
        return jsonify({"error": "You do not have access to this document."}), 403

    if supabase_storage_enabled():
        content = download_from_supabase(row["file_path"])
        return send_file(
            BytesIO(content),
            as_attachment=True,
            download_name=row["original_name"],
            mimetype=row["content_type"],
        )
    return send_from_directory(
        UPLOAD_FOLDER,
        os.path.basename(row["file_name"]),
        as_attachment=True,
        download_name=row["original_name"],
    )


@app.route("/api/projects", methods=["GET", "POST"])
@auth_required
@paid_access_required
def projects(user):
    conn = get_db()
    if request.method == "GET":
        if user["role"] == "admin":
            rows = conn.execute(
                "SELECT * FROM projects ORDER BY created_at DESC"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM projects WHERE user_id = ? ORDER BY created_at DESC",
                (user["id"],),
            ).fetchall()
        projects_data = [serialize_project(conn, row) for row in rows]
        conn.close()
        return jsonify({"projects": projects_data})

    data = request.get_json(silent=True) or {}
    name = str(data.get("name") or "").strip()
    description = str(data.get("description") or "").strip()
    if not name:
        return jsonify({"error": "Project name is required."}), 400

    project_id = conn.execute(
        "INSERT INTO projects (user_id, name, description, category, status, priority, progress) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user["id"], name, description, data.get("category", "Automation"), data.get("status", "In progress"), data.get("priority", "Medium"), 0),
    ).lastrowid
    conn.commit()
    project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    project_data = serialize_project(conn, project)
    conn.close()
    return jsonify({"project": project_data}), 201


@app.route("/api/projects/<int:project_id>", methods=["PUT", "DELETE"])
@auth_required
@paid_access_required
def project_detail(user, project_id):
    conn = get_db()
    existing = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not existing:
        conn.close()
        return jsonify({"error": "Project not found."}), 404

    if user["role"] != "admin" and existing["user_id"] != user["id"]:
        conn.close()
        return jsonify({"error": "You do not have access to this project."}), 403

    if request.method == "PUT":
        data = request.get_json(silent=True) or {}
        conn.execute(
            "UPDATE projects SET name = ?, description = ?, category = ?, status = ?, priority = ?, progress = ? WHERE id = ?",
            (
                str(data.get("name") or existing["name"]).strip(),
                str(data.get("description") or existing["description"] or "").strip(),
                data.get("category", existing["category"]),
                data.get("status", existing["status"]),
                data.get("priority", existing["priority"]),
                existing["progress"],
                project_id,
            ),
        )
        conn.commit()
        project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        project_data = serialize_project(conn, project)
        conn.close()
        return jsonify({"project": project_data})

    conn.execute("DELETE FROM tasks WHERE project_id = ?", (project_id,))
    conn.execute("DELETE FROM milestones WHERE project_id = ?", (project_id,))
    conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/api/tasks", methods=["GET", "POST"])
@auth_required
@paid_access_required
def tasks(user):
    conn = get_db()
    if request.method == "GET":
        if user["role"] == "admin":
            rows = conn.execute("SELECT * FROM tasks ORDER BY created_at DESC").fetchall()
        else:
            rows = conn.execute("SELECT * FROM tasks WHERE user_id = ? ORDER BY created_at DESC", (user["id"],)).fetchall()
        tasks_data = [dict(row) for row in rows]
        conn.close()
        return jsonify({"tasks": tasks_data})

    data = request.get_json(silent=True) or {}
    title = str(data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "Task title is required."}), 400

    project_id = data.get("project_id")
    if not isinstance(project_id, int):
        conn.close()
        return jsonify({"error": "Select a project for this task."}), 400
    project = user_can_access_project(conn, user, project_id)
    if project is False:
        conn.close()
        return jsonify({"error": "You do not have access to this project."}), 403
    if project is None:
        conn.close()
        return jsonify({"error": "Project not found."}), 404
    task_id = conn.execute(
        "INSERT INTO tasks (project_id, user_id, title, status, owner) VALUES (?, ?, ?, ?, ?)",
        (project_id, user["id"], title, data.get("status", "Queued"), data.get("owner", user["full_name"])),
    ).lastrowid
    conn.commit()
    task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    return jsonify({"task": dict(task)})


@app.route("/api/milestones", methods=["GET", "POST"])
@auth_required
@paid_access_required
def milestones(user):
    conn = get_db()
    if request.method == "GET":
        if user["role"] == "admin":
            rows = conn.execute("SELECT * FROM milestones ORDER BY created_at DESC").fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM milestones WHERE user_id = ? ORDER BY created_at DESC",
                (user["id"],),
            ).fetchall()
        conn.close()
        return jsonify({"milestones": [dict(row) for row in rows]})

    data = request.get_json(silent=True) or {}
    title = str(data.get("title") or "").strip()
    project_id = data.get("project_id")
    if not title or not isinstance(project_id, int):
        conn.close()
        return jsonify({"error": "Milestone title and project are required."}), 400
    project = user_can_access_project(conn, user, project_id)
    if project is False:
        conn.close()
        return jsonify({"error": "You do not have access to this project."}), 403
    if project is None:
        conn.close()
        return jsonify({"error": "Project not found."}), 404
    progress = max(0, min(100, int(data.get("progress", 0))))
    milestone_id = conn.execute(
        "INSERT INTO milestones (project_id, user_id, title, status, progress, due_date) VALUES (?, ?, ?, ?, ?, ?)",
        (project_id, user["id"], title, data.get("status", "Planned"), progress, data.get("due_date")),
    ).lastrowid
    conn.commit()
    milestone = conn.execute("SELECT * FROM milestones WHERE id = ?", (milestone_id,)).fetchone()
    conn.close()
    return jsonify({"milestone": dict(milestone)}), 201


@app.route("/api/milestones/<int:milestone_id>", methods=["PUT", "DELETE"])
@auth_required
@paid_access_required
def milestone_detail(user, milestone_id):
    conn = get_db()
    existing = conn.execute("SELECT * FROM milestones WHERE id = ?", (milestone_id,)).fetchone()
    if not existing:
        conn.close()
        return jsonify({"error": "Milestone not found."}), 404
    if user["role"] != "admin" and existing["user_id"] != user["id"]:
        conn.close()
        return jsonify({"error": "You do not have access to this milestone."}), 403

    if request.method == "PUT":
        data = request.get_json(silent=True) or {}
        progress = max(0, min(100, int(data.get("progress", existing["progress"]))))
        conn.execute(
            "UPDATE milestones SET title = ?, status = ?, progress = ?, due_date = ? WHERE id = ?",
            (
                str(data.get("title") or existing["title"]).strip(),
                data.get("status", existing["status"]),
                progress,
                data.get("due_date", existing["due_date"]),
                milestone_id,
            ),
        )
        conn.commit()
        milestone = conn.execute("SELECT * FROM milestones WHERE id = ?", (milestone_id,)).fetchone()
        conn.close()
        return jsonify({"milestone": dict(milestone)})

    conn.execute("DELETE FROM milestones WHERE id = ?", (milestone_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/api/tasks/<int:task_id>", methods=["PUT", "DELETE"])
@auth_required
@paid_access_required
def task_detail(user, task_id):
    conn = get_db()
    existing = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if not existing:
        conn.close()
        return jsonify({"error": "Task not found."}), 404

    if user["role"] != "admin" and existing["user_id"] != user["id"]:
        conn.close()
        return jsonify({"error": "You do not have access to this task."}), 403

    if request.method == "PUT":
        data = request.get_json(silent=True) or {}
        conn.execute(
            "UPDATE tasks SET title = ?, status = ?, owner = ? WHERE id = ?",
            (
                str(data.get("title") or existing["title"]).strip(),
                data.get("status", existing["status"]),
                data.get("owner", existing["owner"]),
                task_id,
            ),
        )
        conn.commit()
        task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        conn.close()
        return jsonify({"task": dict(task)})

    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/api/products", methods=["GET", "POST"])
@auth_required
def products_api(user):
    conn = get_db()
    if request.method == "GET":
        rows = conn.execute("SELECT * FROM products ORDER BY id ASC").fetchall()
        return jsonify({"products": [dict(row) for row in rows]})

    if user["role"] != "admin":
        conn.close()
        return jsonify({"error": "Only administrators can manage products."}), 403

    data = request.get_json(silent=True) or {}
    name = str(data.get("name") or "").strip()
    category = str(data.get("category") or "General").strip()
    price = float(data.get("price") or 0) 
    if not name or price <= 0:
        return jsonify({"error": "Product name and a valid price are required."}), 400

    product_id = conn.execute(
        "INSERT INTO products (name, category, price, rating, description, stock, image) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (name, category, price, float(data.get("rating", 4.8)), data.get("description", ""), int(data.get("stock", 50)), data.get("image", "📦")),
    ).lastrowid
    conn.commit()
    product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    conn.close()
    return jsonify({"product": dict(product)})


@app.route("/api/orders/checkout", methods=["POST"])
@auth_required
def checkout(user):
    if app.config["REQUIRE_PAID_ACCESS"]:
        return jsonify({"error": "Use the verified Stripe checkout flow."}), 403
    data = request.get_json(silent=True) or {}
    items = data.get("items") or []
    if not isinstance(items, list) or not items:
        return jsonify({"error": "Cart is empty."}), 400

    product_ids = [item.get("id") for item in items]
    if not all(isinstance(product_id, int) for product_id in product_ids):
        return jsonify({"error": "Each cart item must reference a valid product."}), 400
    quantities = {product_id: product_ids.count(product_id) for product_id in set(product_ids)}

    conn = get_db()
    placeholders = ",".join("?" for _ in product_ids)
    products_by_id = {
        row["id"]: dict(row)
        for row in conn.execute(
            f"SELECT * FROM products WHERE id IN ({placeholders})", product_ids
        ).fetchall()
    }
    if len(products_by_id) != len(set(product_ids)):
        conn.close()
        return jsonify({"error": "One or more products are no longer available."}), 400

    normalized_items = []
    total = 0.0
    for product_id, quantity in quantities.items():
        product = products_by_id[product_id]
        if product["stock"] < quantity:
            conn.close()
            return jsonify({"error": f"{product['name']} is out of stock."}), 409
        normalized_items.append(
            {
                "id": product["id"],
                "name": product["name"],
                "price": product["price"],
                "quantity": quantity,
            }
        )
        total += float(product["price"]) * quantity

    conn.execute(
        "INSERT INTO orders (user_id, items, total, status) VALUES (?, ?, ?, ?)",
        (user["id"], str(normalized_items), round(total, 2), "paid"),
    )
    for product_id, quantity in quantities.items():
        conn.execute(
            "UPDATE products SET stock = stock - ? WHERE id = ?", (quantity, product_id)
        )
    conn.commit()
    conn.close()
    return jsonify({"message": "Checkout completed successfully.", "total": round(total, 2)})


@app.route("/api/checkout/create-session", methods=["POST"])
@auth_required
def create_checkout_session(user):
    data = request.get_json(silent=True) or {}
    items = data.get("items") or []
    if not isinstance(items, list) or not items:
        return jsonify({"error": "Cart is empty."}), 400

    product_ids = [item.get("id") for item in items]
    if not all(isinstance(product_id, int) for product_id in product_ids):
        return jsonify({"error": "Each cart item must reference a valid product."}), 400
    quantities = {product_id: product_ids.count(product_id) for product_id in set(product_ids)}

    conn = get_db()
    placeholders = ",".join("?" for _ in product_ids)
    products_by_id = {
        row["id"]: dict(row)
        for row in conn.execute(
            f"SELECT * FROM products WHERE id IN ({placeholders})", product_ids
        ).fetchall()
    }
    conn.close()
    if len(products_by_id) != len(set(product_ids)):
        return jsonify({"error": "One or more products are no longer available."}), 400

    line_items = []
    for product_id, quantity in quantities.items():
        product = products_by_id[product_id]
        if product["stock"] < quantity:
            return jsonify({"error": f"{product['name']} is out of stock."}), 409
        line_items.append({
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": product["name"],
                },
                "unit_amount": int(float(product["price"]) * 100),
            },
            "quantity": quantity,
        })

    if app.config["STRIPE_SECRET_KEY"]:
        try:
            app_url = app.config.get("APP_URL", "http://localhost:5000").rstrip("/")
            session = stripe.checkout.Session.create(
                mode="payment",
                line_items=line_items,
                success_url=f"{app_url}?checkout=success",
                cancel_url=f"{app_url}?checkout=cancelled",
                customer_email=user["email"],
                metadata={"user_id": str(user["id"])},
            )
            return jsonify({"checkoutUrl": session.url, "mock": False})
        except Exception as exc:
            return jsonify({"error": f"Stripe checkout failed: {str(exc)}"}), 500

    if app.config["REQUIRE_PAID_ACCESS"]:
        return jsonify({"error": "Online payment is not configured. Add STRIPE_SECRET_KEY before accepting payments."}), 503

    total = sum(
        float(products_by_id[product_id]["price"]) * quantity
        for product_id, quantity in quantities.items()
    )
    conn = get_db()
    conn.execute(
        "INSERT INTO orders (user_id, items, total, status) VALUES (?, ?, ?, ?)",
        (
            user["id"],
            str(
                [
                    {
                        "id": products_by_id[product_id]["id"],
                        "name": products_by_id[product_id]["name"],
                        "price": products_by_id[product_id]["price"],
                        "quantity": quantity,
                    }
                    for product_id, quantity in quantities.items()
                ]
            ),
            round(total, 2),
            "mock_paid",
        ),
    )
    for product_id, quantity in quantities.items():
        conn.execute(
            "UPDATE products SET stock = stock - ? WHERE id = ?", (quantity, product_id)
        )
    conn.commit()
    conn.close()
    return jsonify({"checkoutUrl": None, "mock": True, "message": "Checkout completed successfully.", "total": round(total, 2)})


@app.route("/api/billing/plans")
def billing_plans():
    return jsonify(
        {
            "trialDays": app.config["STRIPE_TRIAL_DAYS"],
            "plans": [
                {"id": plan_id, **plan}
                for plan_id, plan in app.config["BILLING_PLANS"].items()
            ],
        }
    )


@app.route("/api/billing/create-session", methods=["POST"])
@auth_required
def create_billing_session(user):
    data = request.get_json(silent=True) or {}
    plan_id = str(data.get("plan") or "").strip().lower()
    plan = app.config["BILLING_PLANS"].get(plan_id)
    if not plan:
        return jsonify({"error": "Choose a valid billing plan."}), 400
    if not app.config["STRIPE_SECRET_KEY"]:
        return jsonify({"error": "Online payments are not configured yet."}), 503

    try:
        app_url = app.config.get("APP_URL", "http://localhost:5000").rstrip("/")
        line_item = {
            "price_data": {
                "currency": "usd",
                "product_data": {"name": f"CREOVANTA {plan['name']}"},
                "unit_amount": round(plan["price"] * 100),
                "recurring": {"interval": "month"},
            },
            "quantity": 1,
        }
        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[line_item],
            payment_method_collection="always",
            subscription_data={
                "trial_period_days": app.config["STRIPE_TRIAL_DAYS"],
                "metadata": {"user_id": str(user["id"]), "plan": plan_id},
            },
            success_url=f"{app_url}/app?billing=success",
            cancel_url=f"{app_url}/app?billing=cancelled",
            customer_email=user["email"],
            metadata={"user_id": str(user["id"]), "plan": plan_id},
        )
        return jsonify({"checkoutUrl": session.url, "plan": plan_id, "trialDays": app.config["STRIPE_TRIAL_DAYS"]})
    except stripe.error.StripeError as exc:
        return jsonify({"error": f"Stripe checkout failed: {str(exc)}"}), 502


@app.route("/api/stripe/webhook", methods=["POST"])
def stripe_webhook():
    if not app.config["STRIPE_SECRET_KEY"] or not app.config["STRIPE_WEBHOOK_SECRET"]:
        return jsonify({"error": "Stripe webhook is not configured."}), 503
    try:
        event = stripe.Webhook.construct_event(
            request.get_data(),
            request.headers.get("Stripe-Signature", ""),
            app.config["STRIPE_WEBHOOK_SECRET"],
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        return jsonify({"error": "Invalid Stripe webhook."}), 400
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session.get("metadata", {}).get("user_id")
        subscription_id = session.get("subscription")
        plan_id = session.get("metadata", {}).get("plan", "pro")
        if user_id and subscription_id:
            conn = get_db()
            existing = conn.execute(
                "SELECT id FROM subscriptions WHERE stripe_subscription_id = ?", (subscription_id,)
            ).fetchone()
            if not existing:
                conn.execute(
                    "INSERT INTO subscriptions (user_id, stripe_subscription_id, plan, status) VALUES (?, ?, ?, ?)",
                    (int(user_id), subscription_id, plan_id, "trialing"),
                )
            conn.commit()
            conn.close()
    elif event["type"] in {"customer.subscription.updated", "customer.subscription.deleted"}:
        subscription = event["data"]["object"]
        status = subscription.get("status", "canceled")
        if event["type"].endswith("deleted"):
            status = "canceled"
        conn = get_db()
        conn.execute(
            "UPDATE subscriptions SET status = ?, current_period_end = ?, updated_at = CURRENT_TIMESTAMP "
            "WHERE stripe_subscription_id = ?",
            (status, subscription.get("current_period_end"), subscription.get("id")),
        )
        conn.commit()
        conn.close()
    return jsonify({"received": True})


@app.route("/api/admin/summary")
@auth_required
@admin_required
def admin_summary(user):
    conn = get_db()
    total_users = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
    total_projects = conn.execute("SELECT COUNT(*) as c FROM projects").fetchone()["c"]
    total_orders = conn.execute("SELECT COUNT(*) as c FROM orders").fetchone()["c"]
    revenue = conn.execute("SELECT COALESCE(SUM(total), 0) as value FROM orders").fetchone()["value"]
    active_projects = conn.execute("SELECT COUNT(*) as c FROM projects WHERE status IN ('In progress', 'Review')").fetchone()["c"]
    recent_orders = conn.execute("SELECT * FROM orders ORDER BY created_at DESC LIMIT 5").fetchall()
    conn.close()

    return jsonify(
        {
            "metrics": {
                "totalUsers": total_users,
                "totalProjects": total_projects,
                "activeProjects": active_projects,
                "revenue": round(float(revenue), 2),
                "orders": total_orders,
            },
            "recentOrders": [dict(order) for order in recent_orders],
        }
    )


@app.route("/api/ai/chat", methods=["POST"])
@auth_required
@paid_access_required
def ai_chat(user):
    data = request.get_json(silent=True) or {}
    message = str(data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "A message is required."}), 400

    response = generate_ai_reply(message)
    return jsonify({"reply": response})


def generate_ai_reply(message: str) -> str:
    lower = message.lower()

    if OPENAI_API_KEY:
        try:
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "You are CREOVANTA AI, a practical engineering assistant for industrial automation, design, software, and product strategy."},
                    {"role": "user", "content": message},
                ],
                "temperature": 0.7,
            }
            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            }
            response = requests.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers, timeout=20)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            return content.strip()
        except Exception:
            pass

    if any(term in lower for term in ["plc", "ladder", "safety", "automation"]):
        return "Use a staged PLC logic model: safety checks first, conveyor authorization second, sensor validation third, then alarm escalation with event logging. Add HMI indicators and a clear fault recovery sequence before deployment."
    if any(term in lower for term in ["product", "mvp", "roadmap", "launch"]):
        return "Define the smallest valuable delivery: user problem, prototype scope, validation metrics, rollout plan, and quality thresholds. Prioritize reliability and measurable learning before scaling features."
    if any(term in lower for term in ["robot", "packaging", "line", "motion"]):
        return "Evaluate throughput, changeover time, robot reach, guarding, error recovery, and line balancing. Pair robotics with sensor feedback and fault-driven human interventions for better performance."
    return "I can help structure the problem into objective, constraints, system flow, KPIs, and validation steps. Share the operational goal and I’ll turn it into a practical engineering brief."


init_db()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
