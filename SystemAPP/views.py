from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.db.models import Count
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
import csv
import json

from django.db import IntegrityError
from .forms import ContactForm, DepartmentForm, EmployeeForm
from textblob import TextBlob
from .models import Admin, Contact, Department, Employee, EmployeeSignUp, EmployeeFeedback, FinishedTask, Task, PasswordChangeRequest
from .utils import (
    generate_completion_rate_by_employee_plot,
    generate_completed_tasks_over_time_plot,
    generate_employee_performance_plot,
    generate_remaining_tasks_plot,
    generate_task_deadlines_table,
    generate_task_description_wordcloud,
    generate_task_distribution_by_category_plot,
    generate_task_distribution_by_priority_plot,
    generate_task_distribution_plot,
    send_email_to_employee,
)

# Create your views here.

def HOME(request):
    return render(request,"HOME.html")


def REGIEMP(request):
    departments = Department.objects.all()

    if request.method == "POST":
        try:
            # Retrieve form data
            name = request.POST.get("firstname")
            department = request.POST.get("department")
            employee_id = request.POST.get("id")
            address = request.POST.get("address")
            contact_number = request.POST.get("number")
            destination = request.POST.get("dest")
            date_of_birth = request.POST.get("dob")
            date_of_joining = request.POST.get("doj")
            email = request.POST.get("email")
            newemail = request.POST.get("newemail")
            password = request.POST.get("pass")
            designation = request.POST.get("des")
            description = request.POST.get("desc")

            # Save uploaded picture
            if 'pictureInput' in request.FILES:
                picture = request.FILES['pictureInput']
                fs = FileSystemStorage()
                filename = fs.save(picture.name, picture)
                picture_url = fs.url(filename)
            else:
                picture_url = None

            # Send email to employee
            send_email_to_employee(email, newemail)

            # Create and save Employee object
            employee = Employee.objects.create(
                name=name,
                department=department,
                employee_id=employee_id,
                address=address,
                contact_number=contact_number,
                destination=destination,
                date_of_birth=date_of_birth,
                date_of_joining=date_of_joining,
                email=email,
                newemail=newemail,
                password=password,
                designation=designation,
                description=description,
                picture=picture_url  # Assign the URL of the uploaded picture
            )

            # Redirect to the admin dashboard after successful registration
            messages.success(request, "Employee registered successfully!")
            return redirect("AdminDashboard")
        except IntegrityError:
            messages.error(request, "Employee with this Employee ID or Email already exists.")
            return render(request, "REGIEMP.html", {'departments': departments})
        except Exception as e:
            messages.error(request, str(e))
            return render(request, "error.html", {'error_message': str(e)})

    # Render the registration form template for GET requests
    return render(request, "REGIEMP.html", {'departments': departments})


def employeesignuplogin(request):
    if request.method == "POST":
        email = request.POST.get("LOGINEmail")
        password = request.POST.get("LOGINPassword")

        if email and password:
            try:
                user = Employee.objects.get(newemail=email)
                if password == user.password:
                    # Authentication successful
                    request.session['EmployeeEmail'] = email
                    request.session['EmployeeUsername'] = user.name
                    return redirect("EMPDashboard")
                else:
                    return render(request, "LOGIN.html", {'error_message': "Invalid email or password"})
            except Employee.DoesNotExist:
                return render(request, "LOGIN.html", {'error_message': "Invalid email or password"})
        else:
            return render(request, "LOGIN.html", {'error_message': "Please provide email and password"})

    # Render the login page for GET requests
    return render(request, "LOGIN.html")


def handle_login(request, data):
    email = data["Email"]
    password = data["Password"]

    # Authenticate the user
    user = authenticate(request, email=email, password=password)

    if user is not None:
        # Login the user
        login(request, user)
        # Redirect to a success page or homepage
        return redirect("home")
    else:
        # If authentication fails, display an error message for login
        error_message = "Invalid email or password. Please try again."
        return render(request, "login.html", {"error_message": error_message})


def employee_list(request):
    try:
        query = request.GET.get('q')
        if query:
            employees = Employee.objects.filter(email__icontains=query)
        else:
            employees = Employee.objects.all()
        return render(request, 'emplist.html', {'employees': employees, 'query': query})
    except ValidationError as ve:
        # Handle validation errors
        error_message = "Validation Error: {}".format(ve)
        return render(request, "error.html", {'error_message': error_message})
    except Exception as e:
        # Handle other exceptions
        error_message = "An error occurred while processing your request."
        return render(request, "error.html", {'error_message': error_message})



def search_employee(request):
    query_email = request.GET.get('email')
    query_emp_id = request.GET.get('emp_id')

    employees = Employee.objects.all()  # Default queryset

    if query_email:
        employees = employees.filter(email__icontains=query_email)
    if query_emp_id:
        employees = employees.filter(employee_id__icontains=query_emp_id)

    return render(request, 'emplist.html', {'employees': employees, 'query_email': query_email, 'query_emp_id': query_emp_id})


def delete_employee(request, pk):
    employee = Employee.objects.get(pk=pk)
    employee.delete()
    return redirect('AdminDashboard')


def edit_employee(request, pk):
    employee = Employee.objects.get(pk=pk)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            form.save()
            return redirect('AdminDashboard')
    else:
        form = EmployeeForm(instance=employee)
    return render(request, 'editemp.html', {'form': form})

def ABOUT(request):
    return render(request, "ABOUT.html")


def EMPDASHBOARD(request):
    try:
        # Get email from session
        email = request.session.get("EmployeeEmail")

        if email:
            # Lookup the Employee object
            employee = Employee.objects.filter(newemail=email).first()

            # Filter tasks by assigned_to newemail
            tasks = Task.objects.filter(assigned_to__newemail=email)

            # Get total number of tasks
            finished_tasks_count = FinishedTask.objects.filter(assigned_to=employee).count()
            total_tasks = tasks.count() + finished_tasks_count

            # Get number of in-progress tasks with high priority
            in_progress_tasks = tasks.filter(
                status='In Progress',
            ).count()

            # Get number of completed tasks
            completed_tasks = tasks.filter(status='Completed').count() + finished_tasks_count
            total_progress_percent = 100 if total_tasks else 0
            in_progress_percent = round((in_progress_tasks / total_tasks) * 100, 2) if total_tasks else 0
            completed_percent = round((completed_tasks / total_tasks) * 100, 2) if total_tasks else 0

            # Render the template with counts
            return render(request, "EMPDashboard.html", {
                'total_tasks': total_tasks,
                'in_progress_tasks': in_progress_tasks,
                'completed_tasks': completed_tasks,
                'total_progress_percent': total_progress_percent,
                'in_progress_percent': in_progress_percent,
                'completed_percent': completed_percent,
                'employee': employee,
            })
        else:
            # Handle the case where email is not found in the session
            error_message = "Session data missing. Please log in again."
            return render(request, "error.html", {'error_message': error_message})
    except Exception as e:
        error_message = "An error occurred while processing your request."
        return render(request, "error.html", {'error_message': error_message})
    
def logout(request):
    try:
        # Check if the 'admin_email' session variable exists
        if 'admin_email' in request.session:
            # Delete the 'admin_email' session variable
            del request.session['admin_email']

        # Check if other session variables exist and delete them based on conditions
        if 'EmployeeEmail' in request.session:
            del request.session['EmployeeEmail']
        if 'EmployeeUsername' in request.session:
            del request.session['EmployeeUsername']

        # Redirect to the home page after logout
        # Replace 'HOME' with the name of your home page URL pattern
        return redirect('HOME')
    except Exception as e:
        # Handle any exceptions
        error_message = "An error occurred while logging out."
        return render(request, "error.html", {'error_message': error_message})

 
def ADMINLOGIN(request):
    if request.method == "POST":
        admin_id = request.POST.get("email")
        password = request.POST.get("password")

        try:
            # Retrieve admin data based on admin_id
            admin = Admin.objects.get(admin_id=admin_id)
        except Admin.DoesNotExist:
            return redirect("ADMINLOGIN")

        # Check if the provided password matches the admin's password
        if admin.password == password:
            # Create session for admin's email
            request.session['admin_email'] = admin.admin_id

            # Redirect to admin dashboard or render a template
            total_employees = Employee.objects.count()
            return redirect("AdminDashboard")
        else:
            return render(request, "adminlogin.html", {"error_message": "Invalid credentials"})

    # Get the admin email from the session, if available
    admin_email = request.session.get('admin_email', None)

    return render(request, "adminlogin.html", {"admin_email": admin_email})


def AdminDashboard(request):
    try:
        # Check if the 'admin_email' session variable exists
        admin_email = request.session.get('admin_email', None)
        if admin_email is None:
            return redirect('ADMINLOGIN')

        # Total count of employees and departments
        total_employees = Employee.objects.count()
        total_departments = Department.objects.count()

        # Count of finished tasks
        finished_tasks_count = FinishedTask.objects.count()

        # Count of assigned tasks (assuming each employee can have multiple tasks)
        assigned_tasks_count = Task.objects.count()
        dashboard_bar_max = max(assigned_tasks_count, finished_tasks_count, total_departments, 1)
        assigned_tasks_percent = round((assigned_tasks_count / dashboard_bar_max) * 100, 2)
        finished_tasks_percent = round((finished_tasks_count / dashboard_bar_max) * 100, 2)
        departments_percent = round((total_departments / dashboard_bar_max) * 100, 2)

        return render(request, "AdminDashboard.html", {
            'total_employees': total_employees,
            'total_departments': total_departments,
            'finished_tasks_count': finished_tasks_count,
            'assigned_tasks_count': assigned_tasks_count,
            'assigned_tasks_percent': assigned_tasks_percent,
            'finished_tasks_percent': finished_tasks_percent,
            'departments_percent': departments_percent,
            'admin_email': admin_email,
        })
    except Exception as e:
        # Handle any exceptions
        error_message = "An error occurred while loading the admin dashboard."
        return render(request, "error.html", {'error_message': error_message})


def REGIDMENT(request):
    try:
        # Check if the 'admin_email' session variable exists
        admin_email = request.session.get('admin_email', None)
        if admin_email is None:
            return redirect('ADMINLOGIN')

        if request.method == 'POST':
            try:
                form = DepartmentForm(request.POST)
                if form.is_valid():
                    form.save()
                    messages.success(request, "Department added successfully!")
                    return redirect('AdminDashboard')
                else:
                    for error in form.errors.values():
                        messages.error(request, error)
            except IntegrityError:
                messages.error(request, "Department with this name or code already exists.")
        else:
            form = DepartmentForm()
        return render(request, 'REGIDMENT.html', {'form': form, 'admin_email': admin_email})
    except Exception as e:
        # Handle any exceptions
        error_message = "An error occurred while processing department registration: " + str(e)
        return render(request, "error.html", {'error_message': error_message})


def department_list(request):
    query = request.GET.get('name', '')
    if query:
        departments = Department.objects.filter(name__icontains=query)
    else:
        departments = Department.objects.all()
    total_departments = departments.count()
    context = {
        'departments': departments,
        'total_departments': total_departments,
        'query_name': query
    }
    return render(request, 'Dlist.html', context)


# views.py


def edit_department(request, department_id):
    department = get_object_or_404(Department, pk=department_id)
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            return redirect('Dlist')
    else:
        form = DepartmentForm(instance=department)
    return render(request, 'edit_department.html', {'form': form})


def delete_department(request, department_id):
    department = get_object_or_404(Department, pk=department_id)
    department.delete()
    return redirect('Dlist')

# views.pyrender

# views.py


# views.py
def CONTACT(request):
    try:
        if request.method == 'POST':
            form = ContactForm(request.POST)
            if form.is_valid():
                # Save form data
                form.save()
                # Redirect to the home page after successful form submission
                return redirect('HOME')
        else:
            form = ContactForm()
        return render(request, 'CONTACT.html', {'form': form})
    except Exception as e:
        # Handle any exceptions
        error_message = "An error occurred while processing the contact form."
        return render(request, "error.html", {'error_message': error_message})


def assign_task(request):
    if not request.session.get('admin_email'):
        return redirect('ADMINLOGIN')
    if request.method == 'POST':
        title = request.POST['title']
        description = request.POST['description']
        assigned_to = Employee.objects.get(id=request.POST['employee'])
        due_date = request.POST['due_date']

        Task.objects.create(
            title=title,
            description=description,
            assigned_to=assigned_to,
            due_date=due_date,
            status='Pending'
        )

        return redirect('AdminDashboard')

    employees = Employee.objects.all()
    return render(request, 'assigntask.html', {'employees': employees})

def task_des(request):
    users_with_tasks = (
        Employee.objects
        .filter(task__isnull=False)
        .annotate(task_count=Count('task'))
    )
    return render(request, 'TaskDes.html', {'employees': users_with_tasks})

def assigned_tasks(request):
    users_with_tasks = (
        Employee.objects
        .filter(task__isnull=False)
        .annotate(task_count=Count('task'))
        .distinct()
    )
    return render(request, 'taskemployeelist.html', {'employees': users_with_tasks})


def finished_tasks(request):
    finished_tasks = FinishedTask.objects.all()
    return render(request, 'finished_tasks.html', {'finished_tasks': finished_tasks})


def TaskReport(request):
    # Generate plots
    generate_task_distribution_plot()
    generate_remaining_tasks_plot()
    deadline_rows = generate_task_deadlines_table()
    generate_completed_tasks_over_time_plot()
    generate_employee_performance_plot()
    generate_task_description_wordcloud()
    generate_completion_rate_by_employee_plot()
    generate_task_distribution_by_category_plot()
    generate_task_distribution_by_priority_plot()
    # generate_task_duration_distribution_plot()    

    # Add any additional context data you want to pass to the template
    context = {
        'deadline_rows': deadline_rows,
    }

    # Render the template
    return render(request, 'TaskReport.html', context)



def mark_task_finished(request, task_id, email):
    if request.method == 'POST':
        task = get_object_or_404(Task, pk=task_id, assigned_to__email=email)

        # Get the Employee record matching the user's email, fallback if email doesn't exist
        employee = Employee.objects.filter(email=email).first()
        if not employee:
            employee = Employee.objects.filter(id=task.assigned_to.id).first()
        if not employee:
            employee = Employee.objects.first()

        finished_task = FinishedTask.objects.create(
            title=task.title,
            description=task.description,
            assigned_to=employee,          # FinishedTask expects an Employee, not User
            due_date=task.due_date,
            deadline_time=timezone.now().time(),  # Task has no deadline_time, use current time
            email=email,                   # Task has no email field, use the URL param
            finished=True
        )

        task.delete()

        return redirect('AdminDashboard')
    else:
        pass

def DEV(request):
    return render(request, "Developers.html")


def task_end_dates(request):
    tasks = Task.objects.all()
    return render(request, 'taskenddate.html', {'tasks': tasks})

def EMPAccount(request):
    email = request.session.get("EmployeeEmail")
    if not email:
        return redirect("employeesignuplogin")

    employee = Employee.objects.filter(newemail=email).first()

    if request.method == "POST":
        message = request.POST.get("message", "").strip()
        if message and employee:
            polarity = TextBlob(message).sentiment.polarity
            if polarity > 0:
                label = "Positive"
            elif polarity < 0:
                label = "Negative"
            else:
                label = "Neutral"
            EmployeeFeedback.objects.create(
                employee=employee,
                message=message,
                sentiment_score=polarity,
                sentiment_label=label,
            )
            messages.success(request, "Your query has been submitted successfully!")
            return redirect("EMPAccount")

    return render(request, "EMPAccount.html", {"employee": employee})


def TaskDashboard(request):
    # Assuming you get email from session
    email = request.session.get("EmployeeEmail")
    employee = Employee.objects.filter(newemail=email).first()

    # Filter tasks assigned to the employee (using assigned_to relationship)
    assigned_tasks = Task.objects.filter(assigned_to__newemail=email)

    finished_tasks_count = FinishedTask.objects.filter(assigned_to=employee).count()
    total_tasks = assigned_tasks.count() + finished_tasks_count
    completed_tasks = assigned_tasks.filter(status='Completed').count() + finished_tasks_count

    # Calculate completion rate with potential zero division handling
    completion_rate = 0
    if total_tasks > 0:
        if total_tasks == completed_tasks:
            completion_rate = 100  # Set 100% for equal completed and total tasks
        else:
            completion_rate = round((completed_tasks / total_tasks) * 100, 2)
    performance_rate = completion_rate
    NoOfTasks = total_tasks

    context = {
        'completion_rate': completion_rate,
        'total_tasks': NoOfTasks,
        'performance_rate': performance_rate,
        'employee': employee,
    }

    return render(request, "EMPTaskDashboard.html", context)


def EMPTaskEndDate(request):
    try:
        # Check if the 'EmployeeEmail' session variable exists
        email = request.session.get("EmployeeEmail", None)
        if email:
            tasks = Task.objects.filter(assigned_to__newemail=email)
        else:
            tasks = []

        return render(request, 'EMPTaskEndDate.html', {'tasks': tasks})
    except Exception as e:
        # Handle any exceptions
        error_message = "An error occurred while loading the employee tasks."
        return render(request, "error.html", {'error_message': error_message})



def EmployeeTask(request):
    try:
        # Check if the 'EmployeeEmail' session variable exists
        email = request.session.get("EmployeeEmail", None)
        username = request.session.get("EmployeeUsername", None)

        if email:
            tasks = Task.objects.filter(assigned_to__newemail=email)
        else:
            tasks = []

        return render(request, 'EmployeeTask.html', {'email': email, 'tasks': tasks, 'username': username})
    except Exception as e:
        # Handle any exceptions
        error_message = "An error occurred while loading the employee tasks."
        return render(request, "error.html", {'error_message': error_message})

def my_tasks(request):
    email = request.session.get('EmployeeEmail')
    tasks = Task.objects.filter(assigned_to__newemail=email)
    return render(request, 'my_tasks.html', {'tasks': tasks})

def update_status(request, task_id):
    task = Task.objects.get(id=task_id)
    if request.method == 'POST':
        task.status = request.POST['status']
        task.save()
    return redirect('my_tasks')

def admin_settings(request):
    admin_email = request.session.get('admin_email')
    if not admin_email:
        return redirect('ADMINLOGIN')
    admin = Admin.objects.get(admin_id=admin_email)

    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        if new_password:
            admin.password = new_password
            admin.save()
            messages.success(request, "Admin password updated successfully!")
    
    return render(request, 'admin_settings.html', {'admin': admin})

def employee_settings(request):
    email = request.session.get("EmployeeEmail")
    if not email:
        return redirect('employeesignuplogin')
    
    employee = Employee.objects.filter(newemail=email).first()
    
    if request.method == 'POST' and employee:
        new_password = request.POST.get('new_password')
        if new_password:
            PasswordChangeRequest.objects.create(
                employee=employee,
                requested_password=new_password
            )
            messages.success(request, "Password change request submitted successfully!")
            
    requests = PasswordChangeRequest.objects.filter(employee=employee).order_by('-created_at') if employee else []
    return render(request, 'employee_settings.html', {'employee': employee, 'requests': requests})

def password_requests(request):
    admin_email = request.session.get('admin_email')
    if not admin_email:
        return redirect('ADMINLOGIN')
    reqs = PasswordChangeRequest.objects.all().order_by('-created_at')
    return render(request, 'password_requests.html', {'requests': reqs})

def approve_password(request, req_id):
    req = get_object_or_404(PasswordChangeRequest, id=req_id)
    if req.status == 'Pending':
        employee = req.employee
        employee.password = req.requested_password
        employee.save()
        

        req.status = 'Approved'
        req.save()
        messages.success(request, f"Password successfully changed for {employee.name}.")
    return redirect('password_requests')

def reject_password(request, req_id):
    req = get_object_or_404(PasswordChangeRequest, id=req_id)
    if req.status == 'Pending':
        req.status = 'Rejected'
        req.save()
        messages.success(request, "Password request rejected.")
    return redirect('password_requests')


def admin_feedback(request):
    admin_email = request.session.get('admin_email')
    if not admin_email:
        return redirect('ADMINLOGIN')
    feedbacks = EmployeeFeedback.objects.select_related('employee').order_by('sentiment_score')
    counts = {
        'total': feedbacks.count(),
        'positive': feedbacks.filter(sentiment_label='Positive').count(),
        'neutral': feedbacks.filter(sentiment_label='Neutral').count(),
        'negative': feedbacks.filter(sentiment_label='Negative').count(),
    }
    return render(request, 'AdminFeedback.html', {'feedbacks': feedbacks, 'counts': counts})
