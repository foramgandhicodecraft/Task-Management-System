# Task Management System (TMS)

A web-based task management application built with Python and Django. It lets admins assign tasks to employees, track progress, and view performance reports all from one place.

---


## Tech Stack

| Technology | Purpose |
|---|---|
| Python 3.x | Backend language |
| Django 5.x | Web framework |
| SQLite | Database (development) |
| HTML5 / CSS3 | Frontend structure and styling |
| Bootstrap 5 | UI components |
| Font Awesome | Icons |
| JavaScript | Sidebar toggle and interactions |
| Matplotlib / Seaborn | Chart generation |
| Pandas | Data processing |
| WordCloud | Word cloud generation |
| Gmail SMTP | Email notifications |

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/foramgandhicodecraft/Task-Management-System.git
cd Task-Management-System
```

### 2. Create a virtual environment

```bash
python -m venv env
source env/bin/activate        # On Windows: env\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run migrations

```bash
python manage.py migrate
```

### 5. Create an admin record

```bash
python manage.py shell
```

Then inside the shell:

```python
from SystemAPP.models import Admin
Admin.objects.create(admin_id='admin@gmail.com', password='admin123')
exit()
```

### 6. Configure email (optional)

In `TaskManager/settings.py`, set your Gmail credentials:

```python
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your_email@gmail.com'
EMAIL_HOST_PASSWORD = 'your_google_app_password'
```

> Use a Google App Password, not your regular Gmail password. Generate one at myaccount.google.com > Security > App Passwords.

### 7. Run the development server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000` in your browser.

---

### 8. Build & Run docker image

```bash
docker build -t your_docker_username/taskmanagementsystem:latest .
```
```bash
docker run -p 8000:8000 your_docker_username/taskmanagementsystem 
```



