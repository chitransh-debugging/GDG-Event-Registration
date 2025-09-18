from flask import Flask, render_template, request, redirect, url_for, jsonify
import csv
import os

app = Flask(__name__)

# Ensure data folder exists
if not os.path.exists("data"):
    os.makedirs("data")

CSV_FILE = "data/registrations.csv"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        year = request.form["year"]
        branch = request.form["branch"]

        with open(CSV_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([name, email, phone, year, branch])

        return redirect(url_for("success", name=name))
    return render_template("form.html")

@app.route("/success")
def success():
    name = request.args.get("name", "Student")
    return render_template("success.html", name=name)

@app.route("/api/registrations")
def api_registrations():
    registrations = []
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "r") as f:
            reader = csv.reader(f)
            for row in reader:
                if row:
                    registrations.append({
                        "name": row[0],
                        "email": row[1],
                        "phone": row[2],
                        "year": row[3],
                        "branch": row[4]
                    })
    return jsonify(registrations)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
