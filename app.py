import joblib
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, session, url_for, flash
from pymongo import MongoClient
from bson import ObjectId
from decision_engine import decide_leave

app = Flask(__name__)
app.secret_key = "nexus_enterprise_secret_key_2026"

# ---------------- DATABASE ----------------
client = MongoClient("mongodb://localhost:27017/")
db = client["leave_management"]

users = db["users"]
employees = db["employees"]
leaves = db["leaves"]


# ---------------- LOAD MODEL ----------------
try:
    model = joblib.load("model.pkl")
except Exception as e:
    model = None
    print(f"[Notice] Model load notice: {e}")

def smart_decision_ml(features):
    try:
        if model:
            prediction = model.predict([features])[0]
            prob = max(model.predict_proba([features])[0])
            return prediction, prob
    except Exception:
        pass
    return "Approved", 0.82

def get_current_employee():
    """Helper to safely fetch the logged-in employee document."""
    if 'username' not in session:
        return None
    username = session['username']
    return employees.find_one({
        "$or": [{"username": username}, {"name": username}]
    })

# ---------------- HOME ----------------
@app.route('/')
def home():
    all_employees = list(employees.find())
    for emp in all_employees:
        emp["_id"] = str(emp["_id"])
        if not emp.get("avatar"):
            emp["avatar"] = "aarav.jpg"

    today_str = datetime.now().strftime("%Y-%m-%d")
    total_emp = len(all_employees)
    active_leaves = leaves.count_documents({
        "status": "Approved",
        "start_date": {"$lte": today_str},
        "end_date": {"$gte": today_str}
    })
    total_leaves = leaves.count_documents({})
    approved_leaves = leaves.count_documents({"status": "Approved"})
    approval_rate = round((approved_leaves / total_leaves * 100), 1) if total_leaves > 0 else 96.5

    stats = {
        "total_employees": total_emp,
        "active_leaves": active_leaves,
        "total_requests": total_leaves,
        "approval_rate": approval_rate
    }

    return render_template("index.html", employees=all_employees, stats=stats)

# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '').strip()
        position = request.form.get('position', '').strip() or "Software Engineer"
        department = request.form.get('department', '').strip() or "Engineering & Technology"
        contact = request.form.get('contact', '').strip() or "+91 98000 00000"
        location = request.form.get('location', '').strip() or "Bengaluru, India"

        if not username or not password:
            return render_template("register.html", error="Username and password are required")

        if users.find_one({"username": username}):
            return render_template("register.html", error="Username already exists. Please choose another or login.")

        users.insert_one({
            "username": username,
            "password": password,
            "role": "employee"
        })

        emp_count = employees.count_documents({}) + 101
        emp_code = f"NEX-{emp_count}"

        employees.insert_one({
            "name": name if name else username.capitalize(),
            "username": username,
            "position": position,
            "department": department,
            "contact": contact,
            "email": f"{username}@nexuscorp.in",
            "join_date": datetime.now().strftime("%d/%m/%Y"),
            "avatar": "aarav.jpg",
            "emp_code": emp_code,
            "location": location,
            "total_quota": 30
        })

        return redirect('/login')

    return render_template("register.html")

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '').strip()

        user = users.find_one({
            "username": username,
            "password": password
        })

        if user:
            session['username'] = user['username']
            session['role'] = user.get('role', 'employee')

            emp = employees.find_one({"$or": [{"username": username}, {"name": username}]})
            if emp:
                session['display_name'] = emp.get("name", username)
                session['avatar'] = emp.get("avatar", "aarav.jpg")
                session['position'] = emp.get("position", "Team Member")
            else:
                session['display_name'] = "Administrator" if user.get('role') == 'manager' else username
                session['avatar'] = "rohan.jpg" if user.get('role') == 'manager' else "aarav.jpg"
                session['position'] = "Manager / HR Admin" if user.get('role') == 'manager' else "Team Member"

            return redirect('/manager' if user.get('role') == 'manager' else '/dashboard')

        return render_template("login.html", error="Invalid username or password.")

    return render_template("login.html")

# ---------------- DASHBOARD (EMPLOYEE) ----------------
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect('/login')

    emp = get_current_employee()
    if not emp:
        # Check if user is manager visiting dashboard
        if session.get('role') == 'manager':
            return redirect('/manager')
        return "Employee profile not found. Please contact HR or re-register."

    emp_id = emp["_id"]
    data = list(leaves.find({"employee_id": emp_id}).sort("start_date", -1))

    total_quota = emp.get("total_quota", 30)
    approved_days = 0
    pending_count = 0
    approved_count = 0

    for d in data:
        d["_id"] = str(d["_id"])
        dur = float(d.get("duration", 1))
        if d.get("status") == "Approved":
            approved_days += dur
            approved_count += 1
        elif d.get("status") == "Pending":
            pending_count += 1

    remaining_days = max(0, total_quota - approved_days)

    stats = {
        "total_quota": total_quota,
        "used_days": approved_days,
        "remaining_days": remaining_days,
        "pending_count": pending_count,
        "approved_count": approved_count,
        "total_requests": len(data)
    }

    return render_template("dashboard.html", employee=emp, leaves=data, stats=stats)

# ---------------- LEAVE FORM ----------------
@app.route('/leave')
def leave():
    if 'username' not in session:
        return redirect('/login')
    emp = get_current_employee()
    today_str = datetime.now().strftime("%Y-%m-%d")
    return render_template("leave.html", employee=emp, today=today_str)

# ---------------- APPLY LEAVE ----------------
@app.route('/apply_leave', methods=['POST'])
def apply_leave():
    if 'username' not in session:
        return redirect('/login')

    emp = get_current_employee()
    if not emp:
        return "Employee profile not found."

    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    leave_type = request.form.get('leave_type', 'Casual Leave')
    priority = request.form.get('priority', 'Normal')
    reason = request.form.get('reason', 'Personal engagement').strip()
    half_day = 1 if request.form.get('half_day') else 0

    if not start_date or not end_date:
        return "Start date and End date are required."

    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        return "Invalid date format."

    if end_dt < start_dt:
        return "End date cannot be earlier than start date."

    duration = max(1, (end_dt - start_dt).days + 1)
    if half_day:
        duration = 0.5

    history = leaves.count_documents({"employee_id": emp["_id"]})

    last30 = datetime.now() - timedelta(days=30)
    last30_count = leaves.count_documents({
        "employee_id": emp["_id"],
        "start_date": {"$gte": last30.strftime("%Y-%m-%d")}
    })

    prev = leaves.find_one({"employee_id": emp["_id"]}, sort=[("end_date", -1)])
    continuous = 0
    if prev and "end_date" in prev:
        try:
            prev_end = datetime.strptime(prev["end_date"], "%Y-%m-%d")
            if (start_dt - prev_end).days <= 1:
                continuous = 1
        except Exception:
            continuous = 0

    is_monday = 1 if start_dt.weekday() == 0 else 0
    is_friday = 1 if start_dt.weekday() == 4 else 0

    # Execute Hybrid Decision Engine
    status, prob, reasons = decide_leave(
        history=history,
        duration=duration,
        last30=last30_count,
        continuous=continuous,
        is_monday=is_monday,
        is_friday=is_friday,
        leave_type=leave_type,
        priority=priority
    )

    # Insert into database with full metadata
    leaves.insert_one({
        "employee_id": emp["_id"],
        "leave_type": leave_type,
        "start_date": start_date,
        "end_date": end_date,
        "duration": duration,
        "priority": priority,
        "reason": reason if reason else f"{leave_type} request",
        "half_day": half_day,
        "status": status,
        "probability": round(float(prob), 2),
        "reasons": reasons,
        "applied_on": datetime.now().strftime("%Y-%m-%d %H:%M")
    })

    return redirect('/dashboard')

# ---------------- AI DECISION DETAILS ----------------
@app.route('/decision/<leave_id>')
def decision(leave_id):
    try:
        leave = leaves.find_one({"_id": ObjectId(leave_id)})
    except Exception:
        return "Invalid Leave ID"

    if not leave:
        return "Leave record not found"

    emp = employees.find_one({"_id": leave["employee_id"]})
    leave["_id"] = str(leave["_id"])

    reasons = leave.get("reasons", [])
    if not reasons:
        history = leaves.count_documents({"employee_id": leave["employee_id"]})
        dur = float(leave.get("duration", 1))
        if history > 4:
            reasons.append("Historical leave frequency above benchmark")
        if dur > 4:
            reasons.append("Extended absence duration requiring team re-balancing")
        if leave.get("status") == "Approved":
            reasons.append("Complies with statutory company entitlement policies")
        else:
            reasons.append("Awaiting managerial review")

    prob_pct = int(float(leave.get("probability", 0.75)) * 100)

    return render_template("decision.html",
                           leave=leave,
                           reasons=reasons,
                           employee=emp,
                           prob_pct=prob_pct)

# ---------------- MANAGER DASHBOARD ----------------
@app.route('/manager')
def manager():
    if session.get('role') != "manager":
        return redirect('/login')

    search_query = request.args.get('q', '').strip().lower()
    status_filter = request.args.get('status', 'all').capitalize()

    query = {}
    if status_filter != 'All':
        query["status"] = status_filter

    all_leaves = list(leaves.find(query).sort("applied_on", -1))
    employee_map = {e["_id"]: e for e in employees.find()}

    enriched_data = []
    employee_count = {}

    for d in all_leaves:
        d["_id"] = str(d["_id"])
        emp = employee_map.get(d["employee_id"])
        name = emp.get("name", "Unknown") if emp else "Unknown"
        avatar = emp.get("avatar", "aarav.jpg") if emp else "aarav.jpg"
        position = emp.get("position", "Staff") if emp else "Staff"
        dept = emp.get("department", "Operations") if emp else "Operations"

        d["employee_name"] = name
        d["employee_avatar"] = avatar
        d["employee_position"] = position
        d["employee_dept"] = dept

        if search_query:
            if search_query not in name.lower() and search_query not in dept.lower() and search_query not in d.get("leave_type", "").lower():
                continue

        enriched_data.append(d)
        if d.get("status") == "Approved":
            employee_count[name] = employee_count.get(name, 0) + float(d.get("duration", 1))

    top_employee = max(employee_count, key=employee_count.get) if employee_count else "None"
    top_count = employee_count.get(top_employee, 0)

    # Global KPI counts
    total_count = leaves.count_documents({})
    pending_count = leaves.count_documents({"status": "Pending"})
    approved_count = leaves.count_documents({"status": "Approved"})
    rejected_count = leaves.count_documents({"status": "Rejected"})

    stats = {
        "total": total_count,
        "pending": pending_count,
        "approved": approved_count,
        "rejected": rejected_count,
        "top_employee": top_employee,
        "top_count": top_count,
        "auto_approval_rate": round((approved_count / total_count * 100), 1) if total_count > 0 else 92.4
    }

    return render_template("manager.html",
                           leaves=enriched_data,
                           stats=stats,
                           active_filter=status_filter,
                           search_query=search_query)

# ---------------- UPDATE STATUS ----------------
@app.route('/update_status/<id>/<action>')
def update_status(id, action):
    if session.get('role') != "manager":
        return redirect('/login')

    valid_actions = ["Approved", "Rejected", "Pending"]
    if action in valid_actions:
        leaves.update_one({"_id": ObjectId(id)}, {"$set": {"status": action}})
    return redirect(request.referrer or '/manager')

# ---------------- EMPLOYEES DIRECTORY ----------------
@app.route('/employees')
def employees_list():
    if 'username' not in session:
        return redirect('/login')

    all_emps = list(employees.find())
    for emp in all_emps:
        emp["_id"] = str(emp["_id"])
        if not emp.get("avatar"):
            emp["avatar"] = "aarav.jpg"
        # Calculate leaves taken
        approved_leaves = list(leaves.find({"employee_id": ObjectId(emp["_id"]), "status": "Approved"}))
        emp["leaves_taken"] = sum(float(l.get("duration", 1)) for l in approved_leaves)
        emp["remaining_quota"] = max(0, emp.get("total_quota", 30) - emp["leaves_taken"])

    return render_template("employees.html", employees=all_emps)

# ---------------- EMPLOYEE DETAIL ----------------
@app.route('/employee/<emp_id>')
def employee_detail(emp_id):
    if 'username' not in session:
        return redirect('/login')

    try:
        emp = employees.find_one({"_id": ObjectId(emp_id)})
    except Exception:
        return "Invalid Employee ID"

    if not emp:
        return "Employee not found"

    emp["_id"] = str(emp["_id"])
    emp_leaves = list(leaves.find({"employee_id": ObjectId(emp_id)}).sort("start_date", -1))
    for l in emp_leaves:
        l["_id"] = str(l["_id"])

    return render_template("employee_detail.html", emp=emp, leaves=emp_leaves)

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True, port=5000)