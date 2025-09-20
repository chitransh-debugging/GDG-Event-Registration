from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, abort, session
import csv
import os
import io
from openpyxl import Workbook

app = Flask(__name__)

# IMPORTANT: Add a secret key for session management
# In a real app, this should be a long, random string.
app.secret_key = os.environ.get("SECRET_KEY", "my-super-secret-dev-key")

# ensure data folder exists
if not os.path.exists("data"):
    os.makedirs("data")

CSV_FILE = "data/registrations.csv"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "secret123") # Changed from ADMIN_KEY

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        year = request.form.get("year", "").strip()
        branch = request.form.get("branch", "").strip()

        write_header = (not os.path.exists(CSV_FILE)) or (os.path.getsize(CSV_FILE) == 0)
        with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow(["name", "email", "phone", "year", "branch"])
            writer.writerow([name, email, phone, year, branch])
        return redirect(url_for("success", name=name))
    return render_template("form.html")

@app.route("/success")
def success():
    name = request.args.get("name", "Student")
    return render_template("success.html", name=name)

@app.route("/api/registrations")
def api_registrations():
    regs = []
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                regs.append(row)
    return jsonify(regs)

# --- NEW ADMIN LOGIN WORKFLOW ---

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        password = request.form.get("password")
        if password == ADMIN_PASSWORD:
            session['admin'] = True # Set a session variable
            return redirect(url_for("admin"))
        else:
            error = "Invalid password. Please try again."
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.pop('admin', None) # Clear the session variable
    return redirect(url_for('home'))

# UPDATED Admin page (now checks for session)
@app.route("/admin")
def admin():
    if 'admin' not in session: # Check if the user is logged in
        return redirect(url_for('login'))

    regs = []
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                regs.append(row)
    return render_template("admin.html", registrations=regs)

# UPDATED Download routes (now check for session)
@app.route("/admin/download")
def admin_download():
    if 'admin' not in session:
        abort(401)
    if not os.path.exists(CSV_FILE):
        abort(404, description="No registrations yet")
    return send_file(CSV_FILE, as_attachment=True, download_name="registrations.csv", mimetype="text/csv")

@app.route("/admin/download_excel")
def admin_download_excel():
    if 'admin' not in session:
        abort(401)
    if not os.path.exists(CSV_FILE):
        abort(404, description="No registrations yet")

    wb = Workbook()
    ws = wb.active
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            ws.append(row)

    bio = io.BytesIO()
    wb.save(bio)
    bio.seek(0)
    return send_file(bio, as_attachment=True, download_name="registrations.xlsx",
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)