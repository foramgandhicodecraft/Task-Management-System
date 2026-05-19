# Task Management System (TMS)

A web-based task management application built with Python and Django. It lets admins assign tasks to employees, track progress, and view performance reports all from one place.

---

## Author

**Akshit Sheel**

---

## What This Project Does

Managing tasks across a team can get messy quickly. This system gives:

- **Admins** a dashboard to register employees, create departments, assign tasks, and view reports
- **Employees** a personal dashboard to see their tasks and update the status as they work through them

---

## Features

### Admin Side
- Login with a custom session-based system
- Dashboard showing total departments, employees, and task counts
- Register employees (with photo upload and automatic welcome email)
- Add, edit, delete, and search departments
- Assign tasks to employees with a title, description, and due date
- View assigned task lists and upcoming deadlines
- Mark tasks as finished
- Task Report page with auto-generated charts

### Employee Side
- Self-registration and login
- Personal dashboard with task stats
- View all assigned tasks
- Update task status (Pending / In Progress / Completed)
- View upcoming task deadlines
- Performance dashboard with completion rate

### Task Reports (Charts)
- Task distribution among employees
- Remaining vs finished tasks (pie chart)
- Completed tasks over time
- Employee performance comparison
- Task description word cloud
- Completion rate by employee

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

## Project Structure

```
TaskManager/                 # Django project config
│   settings.py              # Database, email, static files config
│   urls.py                  # Root URL configuration
│
SystemAPP/                   # Main application
│   models.py                # All database models
│   views.py                 # All view functions
│   urls.py                  # URL patterns
│   forms.py                 # Django form classes
│   utils.py                 # Chart generation and email utilities
│   admin.py                 # Admin panel registrations
│
│   templates/               # All 18 HTML template files
│   static/
│       css/                 # Custom CSS files
│       IMAGES/              # Static images
│       CHARTS/              # Auto-generated chart images
│       Files/               # task.csv export file
│
│   migrations/              # Database migration files
│
staticfiles/                 # Collected static files
requirements.txt             # Python dependencies
manage.py                    # Django management tool
```

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/akshitsheel/employee-task-management.git
cd employee-task-management
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

---

## Default URLs

| URL | Page |
|---|---|
| `/` | Home page |
| `/ADMINLOGIN` | Admin login |
| `/employeesignuplogin` | Employee login / signup |
| `/ADMINLOGIN/AdminDashboard` | Admin dashboard |
| `/EMPDashboard` | Employee dashboard |
| `/my-tasks/` | Employee task list with status update |
| `/AdminDashboard/TaskReport` | Task analytics and charts |
| `/CONTACT` | Contact page |

---

## Database Models

- **Task** - title, description, assigned_to (User FK), status, due_date, created_at
- **Employee** - name, department, employee_id, email, password, picture, etc.
- **EmployeeSignUp** - name, email, password (for self-registered employees)
- **Department** - name, code, head, location, description
- **FinishedTask** - completed task records
- **Admin** - admin_id, password
- **Contact** - contact form submissions

---

## Known Limitations

- Passwords are currently stored as plain text. Password hashing should be added before deploying to production.
- SQLite is used for development only. Switch to PostgreSQL for production.
- The admin login uses a custom session system, not Django's built-in authentication.

---

## Future Improvements

- Password hashing using Django's built-in system
- Real-time notifications with Django Channels
- Task priority levels (High / Medium / Low)
- Calendar view for deadlines
- REST API for mobile app support
- PostgreSQL for production deployment

---

