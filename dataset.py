import pandas as pd
from pymongo import MongoClient
from datetime import datetime

client = MongoClient("mongodb://localhost:27017/")
db = client["leave_management"]
leaves = db["leaves"]

data = []

for leave in leaves.find():

    emp_id = leave["employee_id"]

    # number_of_leaves
    count = leaves.count_documents({"employee_id": emp_id})

    # duration
    start = datetime.strptime(leave["start_date"], "%Y-%m-%d")
    end = datetime.strptime(leave["end_date"], "%Y-%m-%d")
    duration = (end - start).days

    leave_type = leave.get("leave_type", "Casual")
    priority = leave.get("priority", "Low")
    half_day = 1 if leave.get("half_day") else 0

    # simple pattern
    past_pattern = 1 if count > 3 else 0

    status = leave.get("status", "Pending")

    data.append([
        count, leave_type, duration,
        priority, half_day, past_pattern, status
    ])

df = pd.DataFrame(data, columns=[
    "number_of_leaves",
    "leave_type",
    "duration",
    "priority",
    "half_day",
    "past_pattern",
    "status"
])

df.to_csv("leave_data.csv", index=False)

print("✅ Dataset created")