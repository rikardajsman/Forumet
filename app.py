
import hmac, json, os, re, secrets, threading
from pathlib import Path
from flask import Flask, abort, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__, template_folder=".")
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
                  SESSION_COOKIE_SECURE=os.environ.get("HTTPS_ONLY") == "1")
DATA = Path(__file__).with_name("alpha.json")
CATEGORIES = ("Python", "Web", "Databases", "Career", "Other")
LOCK = threading.Lock()

def load_data():
    try: data = json.loads(DATA.read_text(encoding="utf-8") or "{}")
    except FileNotFoundError: data = {}
    data.setdefault("users", {})
    data.setdefault("posts", [])
    return data

def save_data(data):
    temp = DATA.with_suffix(".tmp")
    temp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    os.replace(temp, DATA)

@app.route("/", methods=["GET", "POST"])
def home():
    error = ""
    token = session.setdefault("csrf", secrets.token_urlsafe(32))
    if request.method == "POST":
        if not hmac.compare_digest(request.form.get("csrf", ""), token): abort(400)
        action, username = request.form.get("action"), request.form.get("username", "").strip().casefold()
        password = request.form.get("password", "")
        with LOCK:
            data = load_data()
            if action == "register":
                if not re.fullmatch(r"[a-z0-9_]{3,24}", username): error = "Username must be 3-24 letters, numbers, or underscores."
                elif len(password) < 12: error = "Password must be at least 12 characters."
                elif username in data["users"]: error = "That username is already taken."
                else: data["users"][username] = generate_password_hash(password); save_data(data)
            elif action == "login":
                hashed = data["users"].get(username, "")
                if not hashed or not check_password_hash(hashed, password): error = "Invalid username or password."
            elif action == "post" and session.get("username"):
                category, message = request.form.get("category"), request.form.get("message", "").strip()
                if category not in CATEGORIES or not message or len(message) > 500: error = "Choose a topic and enter a post of 1-500 characters."
                else:
                    data["posts"].insert(0, {"author": session["username"], "category": category, "message": message})
                    save_data(data); return redirect(url_for("home"))
            elif action == "logout": session.clear(); return redirect(url_for("home"))
            else: error = "Sign in to post."
            if action in ("register", "login") and not error:
                session.clear(); session["username"] = username; session["csrf"] = secrets.token_urlsafe(32)
                return redirect(url_for("home"))
    posts = load_data()["posts"][:100]
    return render_template("index.html", posts=posts, categories=CATEGORIES, error=error)

if __name__ == "__main__": app.run(debug=False)
