from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, abort
import csv
import os
import io
from openpyxl import Workbook

app = Flask(__name__)

# ensure data folder exists
if not os.path.exists("data"):
    os.makedirs("data")

CSV_FILE = "data/registrations.csv"
ADMIN_KEY = os.environ.get("ADMIN_KEY", "admin123")  # change on Render to a secret

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

        # write header if file missing/empty
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

# Admin page (list + download buttons)
@app.route("/admin")
def admin():
    key = request.args.get("key") or request.headers.get("X-Admin-Key")
    if not key or key != ADMIN_KEY:
        abort(401, description="Unauthorized")
    regs = []
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                regs.append(row)
    return render_template("admin.html", registrations=regs, key=key)

# Download CSV (protected)
@app.route("/admin/download")
def admin_download():
    key = request.args.get("key") or request.headers.get("X-Admin-Key")
    if not key or key != ADMIN_KEY:
        abort(401, description="Unauthorized")
    if not os.path.exists(CSV_FILE):
        abort(404, description="No registrations yet")
    return send_file(CSV_FILE, as_attachment=True, download_name="registrations.csv", mimetype="text/csv")

# Download Excel (.xlsx) generated on-the-fly (protected)
@app.route("/admin/download_excel")
def admin_download_excel():
    key = request.args.get("key") or request.headers.get("X-Admin-Key")
    if not key or key != ADMIN_KEY:
        abort(401, description="Unauthorized")
    if not os.path.exists(CSV_FILE):
        abort(404, description="No registrations yet")

    # read CSV and write to Excel in memory
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
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
