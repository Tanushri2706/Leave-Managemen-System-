import random
from datetime import datetime, timedelta
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["leave_management"]

users = db["users"]
employees = db["employees"]
leaves = db["leaves"]

corporate_employees = [
    {
        "name": "Aarav Sharma",
        "username": "aarav.sharma",
        "password": "123",
        "role": "employee",
        "emp_code": "NEX-101",
        "position": "Lead Full Stack Engineer",
        "department": "Engineering & Technology",
        "contact": "+91 98201 44521",
        "email": "aarav.sharma@nexuscorp.in",
        "join_date": "15/01/2022",
        "avatar": "aarav.jpg",
        "total_quota": 30,
        "location": "Bengaluru, India"
    },
    {
        "name": "Priya Patel",
        "username": "priya.patel",
        "password": "123",
        "role": "employee",
        "emp_code": "NEX-102",
        "position": "Senior Product Designer (UI/UX)",
        "department": "Product & Design",
        "contact": "+91 98452 77192",
        "email": "priya.patel@nexuscorp.in",
        "join_date": "02/05/2022",
        "avatar": "priya.jpg",
        "total_quota": 30,
        "location": "Mumbai, India"
    },
    {
        "name": "Rohan Verma",
        "username": "rohan.verma",
        "password": "123",
        "role": "employee",
        "emp_code": "NEX-103",
        "position": "Tech Lead & System Architect",
        "department": "Cloud & Infrastructure",
        "contact": "+91 99104 38201",
        "email": "rohan.verma@nexuscorp.in",
        "join_date": "25/07/2022",
        "avatar": "rohan.jpg",
        "total_quota": 30,
        "location": "Gurugram, India"
    },
    {
        "name": "Sneha Iyer",
        "username": "sneha.iyer",
        "password": "123",
        "role": "employee",
        "emp_code": "NEX-104",
        "position": "HR Operations & People Lead",
        "department": "People & Culture",
        "contact": "+91 98712 99403",
        "email": "sneha.iyer@nexuscorp.in",
        "join_date": "17/04/2023",
        "avatar": "sneha.jpg",
        "total_quota": 30,
        "location": "Chennai, India"
    },
    {
        "name": "Vikram Singh",
        "username": "vikram.singh",
        "password": "123",
        "role": "employee",
        "emp_code": "NEX-105",
        "position": "Senior DevOps & Security Engineer",
        "department": "Infrastructure & SecOps",
        "contact": "+91 97113 55820",
        "email": "vikram.singh@nexuscorp.in",
        "join_date": "09/11/2023",
        "avatar": "vikram.jpg",
        "total_quota": 30,
        "location": "Pune, India"
    },
    {
        "name": "Ananya Roy",
        "username": "ananya.roy",
        "password": "123",
        "role": "employee",
        "emp_code": "NEX-106",
        "position": "AI & Data Science Specialist",
        "department": "Data Science & AI Labs",
        "contact": "+91 98305 66712",
        "email": "ananya.roy@nexuscorp.in",
        "join_date": "13/02/2024",
        "avatar": "ananya.jpg",
        "total_quota": 30,
        "location": "Hyderabad, India"
    }
]

# Ensure Admin Manager
admin_user = users.find_one({"username": "admin"})
if not admin_user:
    users.insert_one({"username": "admin", "password": "admin123", "role": "manager"})

# Upsert corporate employees
for emp_data in corporate_employees:
    u = users.find_one({"username": emp_data["username"]})
    if not u:
        users.insert_one({
            "username": emp_data["username"],
            "password": emp_data["password"],
            "role": "employee"
        })
    
    existing_emp = employees.find_one({"name": emp_data["name"]})
    if not existing_emp:
        existing_emp = employees.find_one({"name": emp_data["username"]})
    
    emp_doc = {
        "name": emp_data["name"],
        "username": emp_data["username"],
        "position": emp_data["position"],
        "department": emp_data["department"],
        "contact": emp_data["contact"],
        "email": emp_data["email"],
        "join_date": emp_data["join_date"],
        "avatar": emp_data["avatar"],
        "emp_code": emp_data["emp_code"],
        "location": emp_data["location"],
        "total_quota": emp_data["total_quota"]
    }
    if existing_emp:
        employees.update_one({"_id": existing_emp["_id"]}, {"$set": emp_doc})
    else:
        employees.insert_one(emp_doc)

# Also ensure shalini exists cleanly
shalini_emp = employees.find_one({"name": "shalini"}) or employees.find_one({"username": "shalini"})
if shalini_emp:
    employees.update_one({"_id": shalini_emp["_id"]}, {"$set": {
        "name": "Shalini Mittal",
        "username": "shalini",
        "position": "Associate Software Engineer",
        "department": "Engineering & Technology",
        "contact": "+91 98112 44321",
        "email": "shalini.mittal@nexuscorp.in",
        "join_date": "15/02/2024",
        "avatar": "priya.jpg",
        "emp_code": "NEX-107",
        "location": "Bengaluru, India",
        "total_quota": 30
    }})

# Seed sample realistic leaves if leaves collection is empty
if leaves.count_documents({}) == 0:
    all_emps = list(employees.find())
    sample_records = [
        ("Aarav Sharma", "Casual Leave", 2, "Normal", "Family occasion at hometown", "Approved", 0.88, 14),
        ("Priya Patel", "Privilege Leave", 4, "Normal", "Annual vacation trip", "Approved", 0.84, 25),
        ("Rohan Verma", "Sick Leave", 1, "Urgent", "Severe viral fever and medical rest", "Approved", 0.92, 7),
        ("Sneha Iyer", "Casual Leave", 3, "Normal", "Attending sister's wedding ceremony", "Pending", 0.65, -2),
        ("Vikram Singh", "Work From Home", 2, "Normal", "Residential broadband maintenance", "Approved", 0.90, -5),
        ("Ananya Roy", "Casual Leave", 5, "Normal", "Personal personal commitments", "Pending", 0.60, -1),
    ]

    base_date = datetime.now()
    for name, ltype, dur, priority, reason, status, prob, offset_days in sample_records:
        target_emp = next((e for e in all_emps if e.get("name") == name or e.get("username") == name.lower().replace(" ", ".")), None)
        if target_emp:
            s_date = base_date + timedelta(days=offset_days)
            e_date = s_date + timedelta(days=dur - 1)
            leaves.insert_one({
                "employee_id": target_emp["_id"],
                "leave_type": ltype,
                "start_date": s_date.strftime("%Y-%m-%d"),
                "end_date": e_date.strftime("%Y-%m-%d"),
                "duration": dur,
                "priority": priority,
                "reason": reason,
                "status": status,
                "probability": prob,
                "applied_on": (s_date - timedelta(days=3)).strftime("%Y-%m-%d %H:%M")
            })

print("[OK] Corporate Database Seeded Successfully!")
