from django.db import models
from django.conf import settings

class Task(models.Model):
    STATUS_CHOICES = [
        ("DONE", "Done"),
        ("IN_PROGRESS", "In Progress"),
        ("COMPLETED", "Completed"),
    ]
    supervisor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tasks_created")
    intern = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tasks_assigned")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="IN_PROGRESS")
    star_rating = models.PositiveSmallIntegerField(null=True, blank=True)  # 1..5
    supervisor_feedback = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class TaskReport(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="reports")
    intern = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="task_reports")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class Attendance(models.Model):
    intern = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="attendance")
    created_at = models.DateTimeField(auto_now_add=True)
    in_office = models.BooleanField(default=False)
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)
    office_distance_m = models.FloatField(null=True, blank=True)
    location_validated = models.BooleanField(default=False)

class Complaint(models.Model):
    STATUS_CHOICES = [("OPEN","Open"),("IN_REVIEW","In Review"),("RESOLVED","Resolved")]
    intern = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="complaints_made")
    supervisor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="complaints_received")
    subject = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="OPEN")
    created_at = models.DateTimeField(auto_now_add=True)

class ActivityLog(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="activity_logs")
    action = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
