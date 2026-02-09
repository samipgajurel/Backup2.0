from datetime import date
from django.db.models import Count
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from accounts.permissions import IsAdmin, IsSupervisor, IsIntern
from accounts.models import User
from .models import Task, TaskReport, Attendance, Complaint, ActivityLog
from .serializers import (
    TaskSerializer, TaskReportSerializer, AttendanceSerializer,
    ComplaintSerializer, ActivityLogSerializer
)

def log(actor, action):
    ActivityLog.objects.create(actor=actor, action=action)

# ---------- ADMIN DASHBOARD (analytics) ----------
class AdminAnalyticsView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        interns = User.objects.filter(role="INTERN").count()
        supervisors = User.objects.filter(role="SUPERVISOR").count()
        tasks_total = Task.objects.count()
        complaints_open = Complaint.objects.filter(status="OPEN").count()

        # monthly task completion counts
        monthly = Task.objects.filter(status="COMPLETED").values("created_at__year","created_at__month").annotate(c=Count("id")).order_by("created_at__year","created_at__month")

        return Response({
            "counts": {
                "interns": interns,
                "supervisors": supervisors,
                "tasks_total": tasks_total,
                "complaints_open": complaints_open,
            },
            "monthly_completed": list(monthly)
        })

# ---------- SUPERVISOR ----------
class SupervisorMyInternsView(APIView):
    permission_classes = [IsSupervisor]
    def get(self, request):
        interns = User.objects.filter(role="INTERN", intern_profile__supervisor=request.user)
        return Response([{"id": i.id, "email": i.email, "full_name": i.full_name} for i in interns])

class SupervisorCreateTaskView(APIView):
    permission_classes = [IsSupervisor]
    def post(self, request):
        intern_id = request.data.get("intern")
        intern = User.objects.filter(id=intern_id, role="INTERN").first()
        if not intern:
            return Response({"detail": "Invalid intern"}, status=400)

        # ensure this intern belongs to supervisor
        if intern.intern_profile.supervisor_id != request.user.id:
            return Response({"detail": "Not your intern"}, status=403)

        ser = TaskSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        task = ser.save(supervisor=request.user, intern=intern)
        log(request.user, f"Created task '{task.title}' for {intern.email}")
        return Response(TaskSerializer(task).data, status=201)

class SupervisorTasksView(APIView):
    permission_classes = [IsSupervisor]
    def get(self, request):
        tasks = Task.objects.filter(supervisor=request.user).order_by("-created_at")
        return Response(TaskSerializer(tasks, many=True).data)

class SupervisorRateTaskView(APIView):
    permission_classes = [IsSupervisor]
    def post(self, request, task_id):
        task = Task.objects.filter(id=task_id, supervisor=request.user).first()
        if not task:
            return Response({"detail":"Not found"}, status=404)

        rating = int(request.data.get("star_rating", 0))
        feedback = request.data.get("supervisor_feedback","")
        if rating < 1 or rating > 5:
            return Response({"detail":"Rating must be 1-5"}, status=400)

        task.star_rating = rating
        task.supervisor_feedback = feedback
        task.save()
        log(request.user, f"Rated task '{task.title}' ({rating} stars)")
        return Response(TaskSerializer(task).data)

class SupervisorInternAttendanceView(APIView):
    permission_classes = [IsSupervisor]
    def get(self, request, intern_id):
        intern = User.objects.filter(id=intern_id, role="INTERN").first()
        if not intern or intern.intern_profile.supervisor_id != request.user.id:
            return Response({"detail":"Not allowed"}, status=403)
        att = Attendance.objects.filter(intern=intern).order_by("-date")[:60]
        return Response(AttendanceSerializer(att, many=True).data)

# ---------- INTERN ----------
class InternMyTasksView(APIView):
    permission_classes = [IsIntern]
    def get(self, request):
        tasks = Task.objects.filter(intern=request.user).order_by("-created_at")
        return Response(TaskSerializer(tasks, many=True).data)

class InternUpdateTaskStatusView(APIView):
    permission_classes = [IsIntern]
    def post(self, request, task_id):
        task = Task.objects.filter(id=task_id, intern=request.user).first()
        if not task:
            return Response({"detail":"Not found"}, status=404)

        status_value = request.data.get("status")
        if status_value not in ["TODO","IN_PROGRESS","COMPLETED"]:
            return Response({"detail":"Invalid status"}, status=400)

        task.status = status_value
        task.save()
        log(request.user, f"Updated task '{task.title}' status to {status_value}")
        return Response(TaskSerializer(task).data)

class InternCreateReportView(APIView):
    permission_classes = [IsIntern]
    def post(self, request, task_id):
        task = Task.objects.filter(id=task_id, intern=request.user).first()
        if not task:
            return Response({"detail":"Not found"}, status=404)

        ser = TaskReportSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        report = ser.save(task=task, intern=request.user)
        log(request.user, f"Submitted report for task '{task.title}'")
        return Response(TaskReportSerializer(report).data, status=201)

class InternMarkAttendanceView(APIView):
    permission_classes = [IsIntern]
    def post(self, request):
        # One per day
        today = date.today()
        in_office = bool(request.data.get("in_office", False))
        office_location = request.data.get("office_location","Codavatar Tech Office")
        intern_location = request.data.get("intern_location","")

        obj, created = Attendance.objects.get_or_create(
            intern=request.user, date=today,
            defaults={
                "in_office": in_office,
                "office_location": office_location,
                "intern_location": intern_location,
            }
        )
        if not created:
            obj.in_office = in_office
            obj.office_location = office_location
            obj.intern_location = intern_location
            obj.save()

        log(request.user, f"Marked attendance (in_office={in_office})")
        return Response(AttendanceSerializer(obj).data)

class InternMySupervisorView(APIView):
    permission_classes = [IsIntern]
    def get(self, request):
        sup = request.user.intern_profile.supervisor
        if not sup:
            return Response({"detail":"No supervisor assigned"}, status=200)
        return Response({"id": sup.id, "email": sup.email, "full_name": sup.full_name})

class InternComplaintView(APIView):
    permission_classes = [IsIntern]
    def post(self, request):
        ser = ComplaintSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        supervisor = request.user.intern_profile.supervisor
        complaint = ser.save(intern=request.user, supervisor=supervisor)
        log(request.user, f"Created complaint '{complaint.subject}'")
        return Response(ComplaintSerializer(complaint).data, status=201)

    def get(self, request):
        qs = Complaint.objects.filter(intern=request.user).order_by("-created_at")
        return Response(ComplaintSerializer(qs, many=True).data)

# ---------- Supervisor: complaints ----------
class SupervisorComplaintListView(APIView):
    permission_classes = [IsSupervisor]
    def get(self, request):
        qs = Complaint.objects.filter(supervisor=request.user).order_by("-created_at")
        return Response(ComplaintSerializer(qs, many=True).data)

class SupervisorUpdateComplaintStatusView(APIView):
    permission_classes = [IsSupervisor]
    def post(self, request, complaint_id):
        c = Complaint.objects.filter(id=complaint_id, supervisor=request.user).first()
        if not c:
            return Response({"detail":"Not found"}, status=404)
        status_value = request.data.get("status")
        if status_value not in ["OPEN","IN_REVIEW","RESOLVED"]:
            return Response({"detail":"Invalid status"}, status=400)
        c.status = status_value
        c.save()
        log(request.user, f"Updated complaint '{c.subject}' to {status_value}")
        return Response(ComplaintSerializer(c).data)

# ---------- Admin: activity logs ----------
class AdminActivityLogView(APIView):
    permission_classes = [IsAdmin]
    def get(self, request):
        logs = ActivityLog.objects.all().order_by("-created_at")[:200]
        return Response(ActivityLogSerializer(logs, many=True).data)
