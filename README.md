# 🌿 Smart Leave Management System (WorkSphere AI)

An enterprise-grade, AI-assisted Leave Management System featuring an intelligent hybrid decision engine that combines rule-based policies with Scikit-learn machine learning. The system provides real-time analytics and role-based dashboards for employees and HR managers.

---

## 📌 Table of Contents

1. Overview
2. Problem Statement and Purpose
3. System Architecture and Workflow
   - Core Workflow
   - Intelligent Hybrid Decision Engine
   - Machine Learning Pipeline
   - Role-Based Access Control
4. Technology Stack
5. Project Directory Structure
6. Setup and Run Guide
7. Demo Login Credentials
8. Application Routes and Key Features
9. Troubleshooting and FAQs
10. Contributors

---

## 🌟 1. Overview

**Smart Leave Management System (WorkSphere AI)** is an enterprise-oriented web application designed to automate and streamline employee leave requests, approvals, and leave balance tracking.

### ✨ Key Features

- **Employee Portal:** Employees can apply for Casual Leave, Sick Leave, Privilege Leave, and Work From Home (WFH). They can also track their remaining leave quota, review leave history, and view AI-generated decision explanations.
- **Manager / HR Admin Console:** Managers can monitor key performance indicators (KPIs), review auto-approval statistics, view the team leave calendar, search and filter requests, and manually update leave request statuses.
- **Explainable AI Decisions:** Each leave request receives a confidence score and a list of reasons explaining why it was approved, rejected, or marked as pending.
- **Employee Directory:** Displays employee codes (e.g., `NEX-101`), departments, contact information, total leave quotas, and leave usage.
- **Responsive User Interface:** Features a modern glassmorphism-inspired design, custom CSS, notification badges, and interactive cards.
- **Leave Balance Tracking:** The default annual leave quota is 30 days. The remaining balance is calculated by subtracting approved leave days from the total quota.

---

## 🎯 2. Problem Statement and Purpose

Traditional leave management processes are often manual, time-consuming, and difficult to track. Common challenges include:

1. **Manual Delays and Bottlenecks:** Managers must manually review routine requests, such as one-day casual leave or WFH requests, which consumes valuable time.
2. **Lack of Transparency:** Employees may not receive clear explanations when their leave requests are rejected or kept pending.
3. **Repeated Absence Patterns:** Frequent leave requests, consecutive absences, and repeated Monday or Friday leave patterns may go unnoticed in manual systems.
4. **Workload and Project Delivery Risks:** Approving multi-day leave without proper planning can affect team productivity, sprint schedules, and project deadlines.

### 💡 Proposed Solution

- **Faster Processing:** Eligible routine leave requests, emergency health-related requests, and WFH requests can be processed automatically according to configured policies.
- **Risk Detection:** The system identifies patterns such as more than four leave requests within 30 days, consecutive leave requests, and repeated Monday or Friday absences.
- **Automated Decision-Making:** The hybrid decision engine evaluates requests using predefined business rules and machine learning predictions.
- **Transparent Explanations:** The decision page at `/decision/<id>` displays the decision, confidence score, and reasons behind the result.

---

## ⚙️ 3. System Architecture and Workflow

### Core Workflow

```text
[Employee Applies for Leave]
             |
             v
[Compute Context Features]
(Historical Leaves, Last 30 Days Count, Consecutive Days,
Friday/Monday Pattern, Duration, Leave Type, Priority)
             |
             v
[Hybrid Decision Engine]
       |                 |
       v                 v
[Rule-Based Engine] [Machine Learning Classifier]
[decision_engine.py] [RandomForest / model.pkl]
             |
             v
[Generate Decision, Confidence Score, and Reasons]
             |
             v
[Save to MongoDB and Update Employee Quota]
             |
             v
[Employee Dashboard Feedback]
             |
             v
[Manager Console: Review or Override]
```

### Intelligent Hybrid Decision Engine

The `decision_engine.py` module contains structured rules for enforcing leave management policies.

| Category | Trigger Conditions | Decision | Explanation |
|---|---|---|---|
| High-Frequency Leave Requests | More than 4 leave requests in the last 30 days | Rejected (92% confidence) | Exceeds monthly leave-frequency guidelines and may require HR review. |
| Consecutive Leave Risk | Consecutive leave request with a duration greater than 3 days | Rejected (90% confidence) | May affect project delivery and sprint planning. |
| Extended-Weekend Pattern | Monday or Friday leave, leave history greater than 3, and duration of at least 2 days | Rejected (86% confidence) | A repeated extended-weekend pattern has been identified. |
| Leave-Quota Risk | Cumulative leave history greater than 7 and requested duration greater than 5 days | Rejected (94% confidence) | The request may exceed the configured annual leave allocation. |
| Health or Emergency | Priority is `Urgent` or `Critical`, or leave type is `Sick Leave` | Approved (95% confidence) | The request meets the configured health or emergency criteria. |
| Remote Work | Leave type is `Work From Home` | Approved (91% confidence) | Remote work is supported under the configured policies. |
| Low-Impact Casual Leave | One-day leave and leave history of 3 or fewer | Approved (88% confidence) | The request meets the configured casual leave criteria. |
| Managerial Review | Requested leave duration is greater than 3 days | Pending (68% confidence) | Additional review may be required for workload delegation and team coverage. |

*Note: The confidence scores and decisions above reflect the rules documented for this project. Actual behavior depends on the implementation and input data.*

### Machine Learning Pipeline

The system uses machine learning to support automated leave decision-making.

1. **Dataset Generation (`dataset.py`):**
   - Extracts historical leave records from MongoDB.
   - Creates `leave_data.csv` containing structured features such as `number_of_leaves`, `leave_type`, `duration`, `priority`, `half_day`, `past_pattern`, and `status`.

2. **Model Training (`train_model.py`):**
   - Applies one-hot encoding to categorical features such as `leave_type` and `priority`.
   - Trains a `RandomForestClassifier` using Scikit-learn.
   - Saves the trained model as `model.pkl` using `joblib`.

3. **Prediction (`app.py`):**
   - Processes new leave requests.
   - Predicts the leave request status.
   - Estimates the prediction probability to support decision-making.

### Role-Based Access Control

#### Employee Access

- Access to `/dashboard`, `/leave`, and `/decision/<id>`.
- Cannot access the manager dashboard or manager-only status update routes.
- Can view leave history and remaining leave balance.
- The remaining balance is calculated as:

  **Remaining Leave Quota = Total Leave Quota (30 Days) − Approved Leave Days**

#### Manager / HR Access

- Access to the management dashboard at `/manager`.
- View total requests, approved requests, rejected requests, pending requests, top requesting employees, and the auto-approval rate.
- Filter requests by `All`, `Pending`, `Approved`, or `Rejected`.
- Search for employees and review their requests.
- Approve, reject, or mark leave requests as pending.
- Access the employee directory at `/employees`.
- View individual employee profiles at `/employee/<id>`.

---

## 💻 4. Technology Stack

| Component | Technologies |
|---|---|
| Backend | Python 3.10+, Flask, Jinja2, Session-Based Authentication |
| Database | MongoDB, PyMongo, BSON ObjectId |
| Machine Learning | Scikit-learn, RandomForestClassifier |
| Data Processing | Pandas, NumPy, Joblib |
| Frontend | HTML5, CSS3, JavaScript |
| Icons and Fonts | Font Awesome 6, Google Fonts (Inter / Outfit) |

---

## 📂 5. Project Directory Structure

```text
leave_management_system/
│
├── app.py                  # Main Flask application, routes, and authentication
├── decision_engine.py      # Rule-based leave decision logic
├── dataset.py              # Exports MongoDB leave records to leave_data.csv
├── train_model.py          # Trains the Random Forest model and exports model.pkl
├── seed_data.py            # Creates sample employees, users, and leave history
├── leave_data.csv          # Machine learning training dataset
├── model.pkl               # Serialized machine learning model
├── database.db             # Auxiliary SQLite database file, if required
│
├── static/
│   ├── style.css           # Custom styling and responsive interface
│   ├── script.js           # Client-side functionality
│   └── images/             # Employee profile images
│
├── templates/
│   ├── base.html           # Shared layout, navigation, alerts, and footer
│   ├── index.html          # Landing page and key statistics
│   ├── login.html          # Login page for employees and managers
│   ├── register.html       # Employee registration page
│   ├── dashboard.html      # Employee dashboard and leave balance
│   ├── leave.html          # Leave application form
│   ├── decision.html       # AI decision details and explanations
│   ├── manager.html        # Manager dashboard and HR analytics
│   ├── employees.html      # Employee directory
│   └── employee_detail.html # Individual employee profile and leave history
│
└── README.md               # Project documentation
```

---

## 🚀 6. Setup and Run Guide

### Prerequisites

Ensure the following software is installed:

1. **Python 3.10 or later:** [Download Python](https://www.python.org/downloads/)
2. **MongoDB Community Server:** [Download MongoDB](https://www.mongodb.com/try/download/community)
3. **Git (Optional):** Required only if you want to clone the project repository.

Ensure that MongoDB is running on its default port, `27017`.

### Step 1: Navigate to the Project Directory

Open PowerShell, Command Prompt, or Bash and navigate to your project directory.

```bash
cd d:\leave_management_system\leave_management_system
```

Update the path if your project is stored in a different location.

### Step 2: Install Dependencies

Install the required Python packages:

```bash
pip install flask pymongo scikit-learn pandas joblib
```

#### Optional: Create a Virtual Environment

Create the virtual environment:

```bash
python -m venv venv
```

On Windows:

```powershell
.\venv\Scripts\activate
```

On macOS or Linux:

```bash
source venv/bin/activate
```

Install the dependencies inside the activated environment:

```bash
pip install flask pymongo scikit-learn pandas joblib
```

### Step 3: Start MongoDB

Ensure MongoDB is running locally at:

```text
mongodb://localhost:27017/
```

**Windows:**

1. Open `services.msc`.
2. Locate **MongoDB Server**.
3. Verify that the service status is **Running**.

Alternatively, open PowerShell as Administrator and run:

```powershell
net start MongoDB
```

**macOS (Homebrew):**

```bash
brew services start mongodb-community
```

**Linux (systemd):**

```bash
sudo systemctl start mongod
```

### Step 4: Seed the Sample Database

Run the following command to populate MongoDB with sample employees, demo login accounts, and initial leave history:

```bash
python seed_data.py
```

Expected output:

```text
[OK] Corporate Database Seeded Successfully!
```

### Step 5: Train the Machine Learning Model

Generate the `model.pkl` file using the available historical leave dataset:

```bash
python train_model.py
```

Expected output:

```text
[OK] Model trained & saved
```

To refresh the dataset from MongoDB and retrain the model, run:

```bash
python dataset.py
python train_model.py
```

### Step 6: Run the Flask Application

Start the Flask development server:

```bash
python app.py
```

The terminal should display output similar to:

```text
* Serving Flask app 'app'
* Debug mode: on
* Running on http://127.0.0.1:5000
Press CTRL+C to quit
```

Open your browser and visit:

**http://127.0.0.1:5000**

To stop the development server, press `Ctrl+C` in the terminal.

---

## 🔑 7. Demo Login Credentials

The project documentation lists the following demo accounts:

| Role | Username | Password | Access / Description |
|---|---|---|---|
| Manager / HR Admin | `admin` | `admin123` | Full access to the manager dashboard, approvals, and analytics |
| Employee 1 | `aarav.sharma` | `123` | Lead Full Stack Engineer |
| Employee 2 | `priya.patel` | `123` | Senior Product Designer (UI/UX) |
| Employee 3 | `rohan.verma` | `123` | Tech Lead and Cloud Architect |
| Employee 4 | `sneha.iyer` | `123` | HR Operations and People Lead |
| Employee 5 | `vikram.singh` | `123` | Senior DevOps and SecOps |
| Employee 6 | `ananya.roy` | `123` | AI and Data Science Specialist |
| New Employee | Register through `/register` | Choose a password | Create a new employee profile |

*Note: These credentials should be verified against the seeded database before use.*

---

## 🌐 8. Application Routes and Key Features

| URL Route | HTTP Methods | Access Level | Description |
|---|---|---|---|
| `/` | `GET` | Public | Landing page with company statistics and navigation |
| `/register` | `GET`, `POST` | Public | Employee registration and department assignment |
| `/login` | `GET`, `POST` | Public | User authentication and session initialization |
| `/dashboard` | `GET` | Employee | Leave balance, active leave requests, and leave history |
| `/leave` | `GET` | Employee | Leave application form with dates, half-day option, and reason |
| `/apply_leave` | `POST` | Employee | Processes the request, invokes the decision engine, and stores the result |
| `/decision/<leave_id>` | `GET` | Employee / Manager | AI decision report, confidence score, and policy explanations |
| `/manager` | `GET` | Manager | HR dashboard, analytics, pending requests, and filters |
| `/update_status/<id>/<action>` | `GET` | Manager | Updates a request status to approved, rejected, or pending |
| `/employees` | `GET` | Authenticated User | Employee directory and leave balances |
| `/employee/<emp_id>` | `GET` | Authenticated User | Individual employee profile and leave history |
| `/logout` | `GET` | Authenticated User | Clears the current session and redirects to login |

---

## ❓ 9. Troubleshooting and FAQs

### Q1. MongoDB Connection Error

**Error:**

```text
pymongo.errors.ServerSelectionTimeoutError:
localhost:27017: No connection could be made
```

**Solution:** MongoDB may not be running. Start the MongoDB service using `services.msc` on Windows or execute the following command in PowerShell as Administrator:

```powershell
net start MongoDB
```

### Q2. A Required Python Module Is Missing

**Error:**

```text
ModuleNotFoundError: No module named 'flask'
```

A similar error may mention `pandas` or `sklearn`.

**Solution:** Activate the correct Python environment and install the required dependencies:

```bash
pip install flask pymongo scikit-learn pandas joblib
```

### Q3. The `model.pkl` File Is Missing

**Error:**

```text
[Errno 2] No such file or directory: 'model.pkl'
```

**Solution:** Run the training script to generate the model:

```bash
python train_model.py
```

The rule-based fallback engine can continue working without the model file if the fallback behavior is implemented and enabled in the application.

### Q4. Port 5000 Is Already in Use

**Solution:** Change the port in the `app.run()` statement in `app.py`.

For example:

```python
app.run(debug=True, port=5050)
```

Then open:

```text
http://127.0.0.1:5050
```

The exact line number may vary depending on the version of `app.py`.

---

## 👥 10. Contributors

- **Smart Leave Management System Project Team**
- **WorkSphere AI © 2026**

---

**End of Documentation**
