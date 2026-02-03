# Medshare – Medicine Donation & Distribution Platform

## 📌 Project Overview

**Medshare** is a Django-based web application designed to enable safe, transparent, and efficient **donation, sharing, and distribution of unused medicines** between individuals, NGOs, and healthcare partners. The platform connects donors, NGOs, and recipients while ensuring compliance, safety, traceability, and accountability.

The system supports medicine listing, verification, NGO dashboards, user roles, chatbot assistance, notifications, delivery coordination, and intelligent recommendations.

---

## 🎯 Core Objectives

* Reduce medicine wastage
* Help underprivileged communities access medicines
* Digitize NGO medicine distribution
* Enable secure medicine donation workflows
* Provide intelligent medicine recommendations
* Support emergency medicine requests

---

## 🧩 Tech Stack

### Backend

* **Python**
* **Django** (Main Framework)
* **SQLite** (Default DB)
* **Django ORM**

### Frontend

* **HTML5**
* **CSS3**
* **JavaScript**
* Django Templates

### AI / Automation

* LLM Integration (`llm_integration.py`)
* Recommendation System (`recommender.py`)
* Chatbot System (`chatbot_views.py`, `test_chatbot.py`)

### Dev Tools

* Django Admin
* Django Middleware
* Django Signals
* Django Tasks
* Django Tests

---

## 🗂 Project Structure

```
Medshare-main/
│
├── app/                     # Main Django App
│   ├── admin.py
│   ├── apps.py
│   ├── chatbot_views.py     # Chatbot logic
│   ├── context_processors.py
│   ├── decorators.py
│   ├── forms.py
│   ├── llm_integration.py   # AI/LLM integration
│   ├── middleware.py
│   ├── models.py            # Database models
│   ├── recommender.py       # Medicine recommendation engine
│   ├── signals.py           # Django signals
│   ├── tasks.py             # Background tasks
│   ├── urls.py
│   ├── views.py
│   ├── migrations/          # Database migrations
│   └── tests/               # Automated tests
│
├── templates/               # HTML templates
│   ├── signup.html
│   ├── login.html
│   ├── dashboard.html
│   ├── ngo_dashboard.html
│   ├── medicines_map.html
│   ├── request_medicine.html
│   ├── notifications.html
│   ├── user_profile.html
│   └── ...
│
├── static/                  # CSS, JS, Images
│
├── db.sqlite3               # Database
├── manage.py                # Django entry point
├── requirements.txt         # Dependencies
├── integration_test.py
├── test_chatbot.py
├── verify_backend.py
├── populate_test_data.py
├── setup.bat
└── README.md
```

---

## 👥 User Roles

### 👤 Donor

* Add medicine donations
* Track donation status
* View history

### 🏥 NGO

* NGO dashboard
* Accept medicine requests
* Manage inventory
* Distribute medicines
* Emergency handling

### 👨‍⚕️ Recipient

* Search medicines
* Request medicines
* Track delivery

### 🛠 Admin

* System control
* User verification
* Data monitoring
* Reports

---

## 🚀 Features

### 💊 Medicine Management

* Medicine listing
* Expiry validation
* Batch tracking
* Storage condition handling
* Location-based availability

### 🤝 Donation System

* Donation requests
* Donation approvals
* NGO assignment
* Distribution tracking

### 🚚 Delivery System

* Delivery requests
* Partner integration
* Location mapping

### 🧠 AI Features

* Medicine recommendation system
* LLM chatbot assistant
* Smart search
* Automated responses

### 📢 Notification System

* In-app notifications
* Email notifications
* Emergency alerts

### 📊 Dashboards

* User dashboard
* NGO dashboard
* Admin panel

---

## 🤖 Chatbot System

Files:

* `chatbot_views.py`
* `llm_integration.py`
* `test_chatbot.py`

Features:

* Medicine queries
* NGO assistance
* Donation help
* Smart guidance
* AI-powered responses

---

## 🧠 Recommendation Engine

File: `recommender.py`

Capabilities:

* Medicine suggestions
* Similar medicine recommendations
* Need-based suggestions
* Availability matching

---

## 🔐 Security Features

* Authentication system
* Role-based access control
* Middleware protection
* Form validation
* Secure sessions

---

## 🧪 Testing System

Includes:

* Integration tests
* Smoke tests
* Notification tests
* Chatbot tests
* Backend verification

Files:

* `integration_test.py`
* `verify_backend.py`
* `test_chatbot.py`
* `app/tests/`

---

## ⚙️ Installation Guide

### 1️⃣ Clone Repository

```bash
git clone <repo-url>
cd Medshare-main
```

### 2️⃣ Create Virtual Environment

```bash
python -m venv env
env\Scripts\activate  # Windows
source env/bin/activate  # Linux/Mac
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Migrate Database

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5️⃣ Create Superuser

```bash
python manage.py createsuperuser
```

### 6️⃣ Run Server

```bash
python manage.py runserver
```

---

## 🌐 URLs

* Admin Panel: `http://127.0.0.1:8000/admin/`
* Home Page: `http://127.0.0.1:8000/`
* NGO Dashboard: `/ngo-dashboard/`
* User Dashboard: `/dashboard/`

---

## 🧾 Environment Setup

Use `.env` file for:

* Secret keys
* Email configs
* API keys
* AI keys

---

## 📈 Future Enhancements

* Mobile app integration
* Blockchain donation tracking
* OCR medicine scanning
* QR-based medicine verification
* Payment gateway for logistics
* Smart logistics routing

---

## 🏆 Use Cases

* NGO medicine distribution
* Disaster relief support
* Emergency medicine requests
* Rural healthcare support
* Hospital waste reduction

---

## 📄 License

This project is for **educational and research purposes**.

---

## 👨‍💻 Developed By

**Medshare Team**

Team members
Adarsh Raj
Piyush Gupta
Shilpi Kumari
Satyam Kr Suman
---

## 📬 Support

For issues, features, or contributions:

* Open an issue
* Submit a pull request

---

> "Medshare is not just a platform, it's a mission to save lives by saving medicines." ❤️
