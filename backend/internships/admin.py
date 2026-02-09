from django.contrib import admin
from .models import Task, TaskReport, Attendance, Complaint, ActivityLog

admin.site.register(Task)
admin.site.register(TaskReport)
admin.site.register(Attendance)
admin.site.register(Complaint)
admin.site.register(ActivityLog)
