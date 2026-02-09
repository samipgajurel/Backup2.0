from django.urls import path

from .views_admin import (
    AdminAnalyticsView, AdminActivityLogView,
    AdminAssignmentsData, AdminAssignIntern, AdminUnassignIntern,
    AdminAttendanceView, AdminComplaintsView, AdminProgressView,
    AdminMonthlyReportCSV, AdminMonthlyReportPDF,
)
from .views_supervisor import (
    SupervisorInternListView, SupervisorTaskCreate, SupervisorTasks, SupervisorRateTask,
    SupervisorAttendanceView, SupervisorReportsView,
    SupervisorComplaintList, SupervisorComplaintUpdateStatus,
)
from .views_intern import (
    InternMySupervisor, InternMyTasks, InternUpdateTaskStatus, InternSubmitTaskReport,
    InternMarkAttendance, InternComplaints,
)

urlpatterns = [
    # ADMIN
    path("admin/analytics/", AdminAnalyticsView.as_view()),
    path("admin/activity/", AdminActivityLogView.as_view()),
    path("admin/assignments/data/", AdminAssignmentsData.as_view()),
    path("admin/assignments/assign/", AdminAssignIntern.as_view()),
    path("admin/assignments/unassign/", AdminUnassignIntern.as_view()),
    path("admin/attendance/", AdminAttendanceView.as_view()),
    path("admin/complaints/", AdminComplaintsView.as_view()),
    path("admin/progress/", AdminProgressView.as_view()),
    path("admin/reports/monthly/csv/", AdminMonthlyReportCSV.as_view()),
    path("admin/reports/monthly/pdf/", AdminMonthlyReportPDF.as_view()),

    # SUPERVISOR
    path("supervisor/interns/", SupervisorInternListView.as_view()),
    path("supervisor/tasks/create/", SupervisorTaskCreate.as_view()),
    path("supervisor/tasks/", SupervisorTasks.as_view()),
    path("supervisor/tasks/<int:task_id>/rate/", SupervisorRateTask.as_view()),
    path("supervisor/attendance/", SupervisorAttendanceView.as_view()),
    path("supervisor/reports/", SupervisorReportsView.as_view()),
    path("supervisor/complaints/", SupervisorComplaintList.as_view()),
    path("supervisor/complaints/<int:complaint_id>/status/", SupervisorComplaintUpdateStatus.as_view()),

    # INTERN
    path("intern/supervisor/", InternMySupervisor.as_view()),
    path("intern/tasks/", InternMyTasks.as_view()),
    path("intern/tasks/<int:task_id>/status/", InternUpdateTaskStatus.as_view()),
    path("intern/tasks/<int:task_id>/report/", InternSubmitTaskReport.as_view()),
    path("intern/attendance/mark/", InternMarkAttendance.as_view()),
    path("intern/complaints/", InternComplaints.as_view()),
]
