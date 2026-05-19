# utils.py
import os
from collections import Counter

from .models import Task, FinishedTask, Employee
import seaborn as sns
import matplotlib.colors as mcolors
import numpy as np
from django.db.models import Count
from django.core.mail import send_mail
from django.conf import settings
from .models import Task, FinishedTask
import matplotlib.pyplot as plt
from django_pandas.io import read_frame
from wordcloud import WordCloud
import pandas as pd
from .models import Task, FinishedTask
from django.db.models import Count
import datetime
from django.utils import timezone
import matplotlib
matplotlib.use('Agg')  # Use the 'Agg' backend which is non-interactive

CHART_DIR = os.path.join('SystemAPP', 'static', 'CHARTS')


def _chart_path(filename):
    os.makedirs(CHART_DIR, exist_ok=True)
    return os.path.join(CHART_DIR, filename)


def _save_empty_chart(filename, title, message='No task data available yet.'):
    plt.figure(figsize=(10, 6))
    plt.title(title)
    plt.text(0.5, 0.5, message, ha='center', va='center', fontsize=14)
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(_chart_path(filename))
    plt.close()


# Import plotting functions from utils.py


# Rest of your views.py code...


def send_email_to_employee(email, new_email):
    """
    Sends a customized welcome email to the client upon signup.
    """
    # Extract email settings from Django settings
    from_email = settings.EMAIL_HOST_USER

    # Construct email subject and message
    subject = "Welcome to TaskManager Pvt Ltd."
    message = f"""
    Dear {email},

    I trust this message finds you in good health. It is my distinct pleasure to welcome you to TaskManager Pvt Ltd, an esteemed platform dedicated to excellence.

    Your participation is highly valued, and we are delighted to have you as part of our team.

    Your new email address for communication is: {new_email}

    TaskManager Pvt Ltd, under the leadership of TaskManager, Director, is committed to fostering a transformative and enriching experience. We firmly believe that your presence will contribute significantly to the vibrancy of our community.

    For any inquiries or assistance, please do not hesitate to reach out to TaskManager directly at {from_email}.

    We appreciate your consideration of our invitation and eagerly anticipate the prospect of welcoming you into the TaskManager Pvt Ltd community.

    Best regards,

    TaskManager
    Director, TaskManager Pvt Ltd
    {from_email}
    """
    #send_mail(subject, message, from_email, [email], fail_silently=False)


def generate_task_distribution_plot():
    task_counts = Counter()
    for row in Task.objects.values('assigned_to__name').annotate(count=Count('id')):
        task_counts[row['assigned_to__name'] or 'Unassigned'] += row['count']
    for row in FinishedTask.objects.filter(finished=True).values('assigned_to__name').annotate(count=Count('id')):
        task_counts[row['assigned_to__name'] or 'Unassigned'] += row['count']

    if not task_counts:
        _save_empty_chart('task_distribution.png', 'Task Distribution Among Employees')
        return

    task_counts = pd.Series(task_counts).sort_values(ascending=False)


    plt.figure(figsize=(12, 8))

    # Create gradient colormap from dark blue to light blue
    colormap = plt.cm.Blues
    norm = mcolors.Normalize(vmin=0, vmax=len(task_counts))
    colors = [colormap(norm(i)) for i in range(len(task_counts))]

    bars = task_counts.plot(kind='bar', color=colors, edgecolor='black')

    plt.title('Task Distribution Among Employees', fontsize=16)
    plt.xlabel('Employee', fontsize=14)
    plt.ylabel('Number of Tasks', fontsize=14)

    # Set y-axis to integer scale
    plt.gca().yaxis.set_major_locator(plt.MaxNLocator(integer=True))

    plt.xticks(rotation=45, ha='right', fontsize=12)
    plt.yticks(fontsize=12)

    # Calculate percentiles
    percentiles = np.percentile(task_counts.values, [25, 50, 75])

    # Categorize tasks based on percentiles
    categories = []
    for count in task_counts:
        if count >= percentiles[2]:
            categories.append('Heavy workload')
        elif count >= percentiles[1]:
            categories.append('Moderate workload')
        else:
            categories.append('Light workload')

    # Create legend with colors corresponding to the bars
    legend_handles = []
    for i, (label, color) in enumerate(zip(categories, colors)):
        if label not in legend_handles:
            legend_handles.append(label)
            plt.bar(0, 0, color=color, label=label)  # Dummy bars for legend

    plt.legend(loc='upper right', fontsize=12)

    plt.tight_layout()
    plt.savefig(_chart_path('task_distribution.png'))
    plt.close()


def generate_remaining_tasks_plot():
    active_tasks = Task.objects.count()
    finished_tasks = FinishedTask.objects.filter(finished=True).count()
    total_tasks = active_tasks + finished_tasks
    remaining_tasks = active_tasks

    if total_tasks == 0:
        _save_empty_chart('remaining_tasks.png', 'Remaining Tasks')
        return

    # Calculate percentages
    finished_percentage = (finished_tasks / total_tasks) * 100
    remaining_percentage = 100 - finished_percentage

    labels = [f'Finished ({finished_percentage:.1f}%)',
              f'Remaining ({remaining_percentage:.1f}%)']
    sizes = [finished_tasks, remaining_tasks]
    colors = ['lightblue', 'lightcoral']

    # Explode the first slice to highlight it
    explode = (0.1, 0)

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(aspect="equal"))

    # Create pie chart
    wedges, texts, autotexts = ax.pie(sizes, explode=explode, labels=labels, colors=colors,
                                      autopct='%1.1f%%', startangle=140, shadow=True)

    # Customizing text properties
    ax.legend(wedges, labels, loc="upper left", fontsize=10,
              facecolor='white', edgecolor='black', shadow=True)
    plt.setp(autotexts, size=12, weight="bold")

    plt.title('Remaining Tasks', fontsize=16)

    # Save the plot
    plt.savefig(_chart_path('remaining_tasks.png'))
    plt.close()


def generate_task_deadlines_table():
    # Get the current date and time
    current_date = timezone.now().date()

    # Calculate the date for the next Monday
    next_monday = current_date + datetime.timedelta(days=(7 - current_date.weekday()))

    # Calculate the date for the following Monday
    following_monday = next_monday + datetime.timedelta(weeks=1)

    deadlines_data = (
        Task.objects
        .filter(due_date__gte=next_monday, due_date__lt=following_monday)
        .values('due_date')
        .annotate(num_tasks=Count('id'))
        .order_by('due_date')
    )

    return list(deadlines_data)


def generate_completed_tasks_over_time_plot():
    finished_tasks = (
        FinishedTask.objects
        .filter(finished=True)
        .values('due_date')
        .annotate(count=Count('id'))
        .order_by('due_date')
    )

    if not finished_tasks:
        _save_empty_chart('completed_tasks_over_time.png', 'Completed Tasks Over Time')
        return

    plt.figure(figsize=(10, 6))
    dates = [row['due_date'] for row in finished_tasks]
    counts = [row['count'] for row in finished_tasks]
    plt.plot(dates, counts, marker='o', color='skyblue')

    plt.title('Completed Tasks Over Time')
    plt.xlabel('Deadline Date')
    plt.ylabel('Number of Tasks')
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Add legend
    plt.legend(['Completed Tasks'], loc='upper right', facecolor='lightgrey')

    plt.savefig(_chart_path('completed_tasks_over_time.png'))
    plt.close()


def generate_employee_performance_plot():
    total_counts = Counter()
    completed_counts = Counter()

    for row in Task.objects.values('assigned_to__name').annotate(count=Count('id')):
        total_counts[row['assigned_to__name'] or 'Unassigned'] += row['count']
    for row in FinishedTask.objects.filter(finished=True).values('assigned_to__name').annotate(count=Count('id')):
        name = row['assigned_to__name'] or 'Unassigned'
        total_counts[name] += row['count']
        completed_counts[name] += row['count']

    if not total_counts:
        _save_empty_chart('employee_performance.png', 'Employee Performance')
        return

    performance = pd.DataFrame({
        'employee': list(total_counts.keys()),
        'completion_percentage': [
            (completed_counts[name] / total_counts[name]) * 100 if total_counts[name] else 0
            for name in total_counts.keys()
        ],
    }).sort_values(by='completion_percentage', ascending=False)

    # Plotting
    plt.figure(figsize=(10, 6))
    sns.barplot(x='completion_percentage', y='employee', hue='employee',
                data=performance, palette='coolwarm', legend=False)
    plt.title('Employee Performance')
    plt.xlabel('Completion Percentage')
    plt.ylabel('Employee')
    plt.tight_layout()

    # Save the plot
    plt.savefig(_chart_path('employee_performance.png'))
    plt.close()



def generate_task_description_wordcloud():
    descriptions = ' '.join(
        list(Task.objects.values_list('description', flat=True)) +
        list(FinishedTask.objects.filter(finished=True).values_list('description', flat=True))
    ).strip()

    if not descriptions:
        _save_empty_chart('task_description_wordcloud.png', 'Task Description Word Cloud')
        return

    wordcloud = WordCloud(width=800, height=400,
                          background_color='white').generate(descriptions)

    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.title('Task Description Word Cloud')
    plt.tight_layout()
    plt.savefig(_chart_path('task_description_wordcloud.png'))
    plt.close()


def generate_completion_rate_by_employee_plot():
    total_counts = Counter()
    completed_counts = Counter()

    for row in Task.objects.values('assigned_to__name').annotate(count=Count('id')):
        total_counts[row['assigned_to__name'] or 'Unassigned'] += row['count']
    for row in FinishedTask.objects.filter(finished=True).values('assigned_to__name').annotate(count=Count('id')):
        name = row['assigned_to__name'] or 'Unassigned'
        total_counts[name] += row['count']
        completed_counts[name] += row['count']

    if not total_counts:
        _save_empty_chart('completion_rate_by_employee.png', 'Task Completion Rate by Employee')
        return

    employee_names = list(total_counts.keys())
    completion_rates = [
        (completed_counts[name] / total_counts[name]) * 100 if total_counts[name] else 0
        for name in employee_names
    ]

    plt.figure(figsize=(8, 8))
    plt.bar(employee_names, completion_rates, color='green')
    plt.title('Task Completion Rate by Employee')
    plt.xlabel('Employee')
    plt.ylabel('Completion Rate (%)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(_chart_path('completion_rate_by_employee.png'))
    plt.close()


def generate_task_distribution_by_category_plot():
    category_counts = Counter()
    for row in Task.objects.values('assigned_to__department').annotate(count=Count('id')):
        category_counts[row['assigned_to__department'] or 'Uncategorized'] += row['count']
    for row in FinishedTask.objects.filter(finished=True).values('assigned_to__department').annotate(count=Count('id')):
        category_counts[row['assigned_to__department'] or 'Uncategorized'] += row['count']

    if not category_counts:
        _save_empty_chart('task_distribution_by_category.png', 'Task Distribution by Department')
        return

    labels = list(category_counts.keys())
    counts = list(category_counts.values())

    plt.figure(figsize=(10, 6))
    plt.bar(labels, counts, color=['skyblue', 'lightgreen', 'lightcoral', 'orange', 'plum'])
    plt.title('Task Distribution by Department')
    plt.xlabel('Department')
    plt.ylabel('Number of Tasks')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(_chart_path('task_distribution_by_category.png'))
    plt.close()


def generate_task_distribution_by_priority_plot():
    today = timezone.now().date()
    priority_counts = Counter({'Overdue': 0, 'High': 0, 'Medium': 0, 'Low': 0})

    for due_date in Task.objects.values_list('due_date', flat=True):
        days_left = (due_date - today).days
        if days_left < 0:
            priority_counts['Overdue'] += 1
        elif days_left <= 2:
            priority_counts['High'] += 1
        elif days_left <= 7:
            priority_counts['Medium'] += 1
        else:
            priority_counts['Low'] += 1

    if sum(priority_counts.values()) == 0:
        _save_empty_chart('task_distribution_by_priority.png', 'Task Distribution by Due-Date Priority')
        return

    labels = [label for label, count in priority_counts.items() if count > 0]
    counts = [priority_counts[label] for label in labels]
    colors = {'Overdue': '#ef4444', 'High': '#f97316', 'Medium': '#facc15', 'Low': '#22c55e'}

    plt.figure(figsize=(10, 6))
    plt.bar(labels, counts, color=[colors[label] for label in labels])
    plt.title('Task Distribution by Due-Date Priority')
    plt.xlabel('Priority')
    plt.ylabel('Number of Active Tasks')
    plt.gca().yaxis.set_major_locator(plt.MaxNLocator(integer=True))
    plt.tight_layout()
    plt.savefig(_chart_path('task_distribution_by_priority.png'))
    plt.close()


#def generate_task_distribution_by_category_plot():
#    tasks = Task.objects.all()
#    df_tasks = read_frame(tasks)
#    category_counts = df_tasks['category'].value_counts()

    # Define custom colors for each category
#    colors = ['skyblue', 'lightgreen', 'lightcoral', 'orange']

#    plt.figure(figsize=(10, 6))
#    category_counts.plot(kind='bar', color=colors)
#    plt.title('Task Distribution by Category')
#    plt.xlabel('Category')
#    plt.ylabel('Number of Tasks')
#    plt.xticks(rotation=45)
#    plt.tight_layout()
#    plt.savefig('SystemAPP/static/CHARTS/task_distribution_by_category.png')
#    plt.close()



#def generate_task_distribution_by_priority_plot():
#    tasks = Task.objects.all()
#    df_tasks = read_frame(tasks)
#    priority_counts = df_tasks['priority'].value_counts()

#    plt.figure(figsize=(10, 6))
#    priority_counts.plot(kind='bar', color=['red', 'orange', 'yellow'])
#    plt.title('Task Distribution by Priority')
 #   plt.xlabel('Priority')
#    plt.ylabel('Number of Tasks')
#    plt.xticks(rotation=0)
#    plt.tight_layout()
#    plt.savefig('SystemAPP/static/CHARTS/task_distribution_by_priority.png')
#    plt.close()

# Function to generate task duration distribution histogram


# Function to generate task duration distribution histogram
# def generate_task_duration_distribution_plot():
#     tasks = Task.objects.all()
#     df_tasks = read_frame(tasks)

#     # Drop rows with null values in deadline_date or created_at columns
#     df_tasks = df_tasks.dropna(subset=['deadline_date', 'created_at'])

#     # Convert deadline_date and created_at columns to datetime if not already
#     df_tasks['deadline_date'] = pd.to_datetime(df_tasks['deadline_date'])
#     df_tasks['created_at'] = pd.to_datetime(df_tasks['created_at'])

#     # Calculate task durations in days
#     task_durations = (df_tasks['deadline_date'] -
#                       df_tasks['created_at']).dt.days

#     plt.figure(figsize=(10, 6))
#     plt.hist(task_durations, bins=20)
#     plt.title('Task Duration Distribution')
#     plt.xlabel('Task Duration (days)')
#     plt.ylabel('Frequency')
#     plt.xticks(rotation=0)
#     plt.tight_layout()
#     plt.savefig('task_duration_distribution.png')
#     plt.close()


