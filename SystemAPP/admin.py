from django.contrib import admin

from .forms import DepartmentForm
from .models import Admin, Contact, Department, Employee, EmployeeSignUp, FinishedTask, Task


@admin.register(Admin)
class AdminAdmin(admin.ModelAdmin):
    list_display = ['admin_id']


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'department', 'employee_id', 'address', 'contact_number',
                    'destination', 'date_of_birth', 'date_of_joining', 'email', 'newemail', 'designation', 'description')


@admin.register(EmployeeSignUp)
class EmployeeSignUpAdmin(admin.ModelAdmin):
    list_display = ('name', 'email')


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    form = DepartmentForm


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    # Customize the displayed fields if needed
    list_display = ['first_name', 'last_name',
                    'email', 'mobile', 'message', 'created_at']


# admin.py


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'description',
        'assigned_to',
        'status',
        'due_date',
        'created_at'
    ]



@admin.register(FinishedTask)
class FinishedTaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'description', 'assigned_to',
                    'due_date', 'deadline_time', 'email', 'finished']
