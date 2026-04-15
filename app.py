import joblib
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient
from bson import ObjectId
from decision_engine import decide_leave

app = Flask(__name__)
app.secret_key = "secret"

# ---------------- DATABASE ----------------
client = MongoClient("mongodb://localhost:27017/")
db = client["leave_management"]

users = db["users"]
employees = db["employees"]
leaves = db["leaves"]

# ---------------- DEFAULT USERS ----------------
default_users = [
    {"username": "admin", "password": "admin123", "role": "manager"},
    {"username": "shalini", "password": "123", "role": "employee"}
]

for u in default_users:
    if users.count_documents({"username": u["username"]}) == 0:
        users.insert_one(u)

# ---------------- LOAD MODEL ----------------
model = joblib.load("model.pkl")

def smart_decision_ml(features):
    try:
        prediction = model.predict([features])[0]
        prob = max(model.predict_proba([features])[0])
    except:
        prediction = "Approved"
        prob = 0.8
    return prediction, prob

# ---------------- HOME ----------------
@app.route('/')
def home():
    return render_template("index.html")

# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        position = request.form.get('position')
        contact = request.form.get('contact')

        if users.find_one({"username": username}):
            return "User already exists"

        users.insert_one({
            "username": username,
            "password": password,
            "role": "employee"
        })

        employees.insert_one({
            "name": username,
            "position": position or "Not Set",
            "contact": contact or "Not Set"
        })

        return redirect('/login')

    return render_template("register.html")

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        user = users.find_one({
            "username": request.form.get('username'),
            "password": request.form.get('password')
        })

        if user:
            session['username'] = user['username']
            session['role'] = user['role']

            # AUTO CREATE EMPLOYEE
            if user['role'] == "employee":
                if not employees.find_one({"name": user['username']}):
                    employees.insert_one({
                        "name": user['username'],
                        "position": "Not Set",
                        "contact": "Not Set"
                    })

            return redirect('/manager' if user['role']=="manager" else '/dashboard')

        return "Invalid login"

    return render_template("login.html")

# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect('/login')

    emp = employees.find_one({"name": session['username']})
    if not emp:
        return "Employee not found"

    data = list(leaves.find({"employee_id": emp["_id"]}))

    for d in data:
        d["_id"] = str(d["_id"])

    return render_template("dashboard.html", leaves=data)

# ---------------- LEAVE ----------------
@app.route('/leave')
def leave():
    if 'username' not in session:
        return redirect('/login')
    return render_template("leave.html")

# ---------------- APPLY LEAVE ----------------
@app.route('/apply_leave', methods=['POST'])
def apply_leave():

    if 'username' not in session:
        return redirect('/login')

    emp = employees.find_one({"name": session['username']})

    # 🔥 FIX: prevent crash
    if not emp:
        return "Employee not found. Please register first."

    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')

    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    duration = (end_dt - start_dt).days

    history = leaves.count_documents({"employee_id": emp["_id"]})

    last30 = datetime.now() - timedelta(days=30)
    last30_count = leaves.count_documents({
        "employee_id": emp["_id"],
        "start_date": {"$gte": last30.strftime("%Y-%m-%d")}
    })

    prev = leaves.find_one({"employee_id": emp["_id"]}, sort=[("end_date",-1)])

    continuous = 0
    if prev:
        prev_end = datetime.strptime(prev["end_date"], "%Y-%m-%d")
        if (start_dt - prev_end).days <= 1:
            continuous = 1

    is_monday = 1 if start_dt.weekday() == 0 else 0
    is_friday = 1 if start_dt.weekday() == 4 else 0

    # RULE ENGINE
    status, prob = decide_leave(history, duration, last30_count, continuous, is_monday, is_friday)

    if status is None:
        status, prob = smart_decision_ml([history, duration, last30_count, continuous])

    leaves.insert_one({
        "employee_id": emp["_id"],
        "start_date": start_date,
        "end_date": end_date,
        "status": status,
        "probability": round(float(prob),2)
    })

    return redirect('/dashboard')

# ---------------- AI DECISION ----------------
@app.route('/decision/<leave_id>')
def decision(leave_id):

    leave = leaves.find_one({"_id": ObjectId(leave_id)})

    if not leave:
        return "Leave not found"

    emp = employees.find_one({"_id": leave["employee_id"]})

    history = leaves.count_documents({"employee_id": leave["employee_id"]})

    start_dt = datetime.strptime(leave["start_date"], "%Y-%m-%d")
    end_dt = datetime.strptime(leave["end_date"], "%Y-%m-%d")

    duration = (end_dt - start_dt).days

    reasons = []

    if history > 5:
        reasons.append("High leave history")

    if duration > 5:
        reasons.append("Long duration leave")

    if leave.get("probability", 0) < 0.5:
        reasons.append("Low approval probability")

    if not reasons:
        reasons.append("Normal leave request")

    return render_template("decision.html",
                           leave=leave,
                           reasons=reasons,
                           employee=emp["name"] if emp else "Unknown")

# ---------------- EMPLOYEE LIST ----------------
@app.route('/employees')
def employees_list():

    if session.get('role') != "manager":
        return redirect('/login')

    data = list(employees.find())

    for emp in data:
        emp["_id"] = str(emp["_id"])

    return render_template("employees.html", employees=data)

# ---------------- EMPLOYEE DETAIL ----------------
@app.route('/employee/<emp_id>')
def employee_detail(emp_id):

    if session.get('role') != "manager":
        return redirect('/login')

    emp = employees.find_one({"_id": ObjectId(emp_id)})

    if not emp:
        return "Employee not found"

    emp["_id"] = str(emp["_id"])

    return render_template("employee_detail.html", emp=emp)

# ---------------- MANAGER ----------------
@app.route('/manager')
def manager():

    if session.get('role') != "manager":
        return redirect('/login')

    data = list(leaves.find())
    employee_count = {}

    for d in data:
        d["_id"] = str(d["_id"])

        emp = employees.find_one({"_id": d["employee_id"]})
        name = emp["name"] if emp else "Unknown"

        d["employee_name"] = name
        employee_count[name] = employee_count.get(name, 0) + 1

    top_employee = max(employee_count, key=employee_count.get) if employee_count else "N/A"
    top_count = employee_count.get(top_employee, 0)

    return render_template("manager.html",
                           leaves=data,
                           top_employee=top_employee,
                           top_count=top_count)

# ---------------- UPDATE ----------------
@app.route('/update_status/<id>/<action>')
def update_status(id, action):
    leaves.update_one({"_id": ObjectId(id)}, {"$set": {"status": action}})
    return redirect('/manager')

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)