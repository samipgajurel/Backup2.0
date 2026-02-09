from rest_framework.views import APIView
from rest_framework.response import Response

from accounts.models import User
from .models import Task, Attendance, Complaint, TaskReport, ActivityLog
from .permissions import IsSupervisor
from .serializers import TaskSerializer


class SupervisorInternListView(APIView):
    permission_classes = [IsSupervisor]

    def get(self, request):
        interns = User.objects.filter(role="INTERN", supervisor=request.user).order_by("full_name")
        return Response([{"id": i.id, "full_name": i.full_name, "email": i.email} for i in interns])


class SupervisorTaskCreate(APIView):
    permission_classes = [IsSupervisor]

    def post(self, request):
        intern_id = request.data.get("intern")
        title = (request.data.get("title") or "").strip()
        description = (request.data.get("description") or "").strip()

        if not intern_id or not title:
            return Response({"detail": "intern and title required"}, status=400)

        try:
            intern = User.objects.get(id=intern_id, role="INTERN", supervisor=request.user)
        except User.DoesNotExist:
            return Response({"detail": "Intern not found / not assigned to you"}, status=404)

        task = Task.objects.create(
            supervisor=request.user,
            intern=intern,
            title=title,
            description=description,
            status="IN_PROGRESS",  # default
        )

        ActivityLog.objects.create(actor=request.user, action=f"Created task {task.id} for {intern.email}")
        return Response(TaskSerializer(task).data, status=201)


class SupervisorTasks(APIView):
    permission_classes = [IsSupervisor]

    def get(self, request):
        qs = Task.objects.filter(supervisor=request.user).select_related("intern", "supervisor").order_by("-created_at")
        return Response(TaskSerializer(qs, many=True).data)


class SupervisorRateTask(APIView):
    permission_classes = [IsSupervisor]

    def post(self, request, task_id):
        star_rating = request.data.get("star_rating")
        supervisor_feedback = (request.data.get("supervisor_feedback") or "").strip()

        try:
            star_rating = int(star_rating)
        except (TypeError, ValueError):
            return Response({"detail": "star_rating must be an integer 1-5"}, status=400)

        if star_rating < 1 or star_rating > 5:
            return Response({"detail": "star_rating must be 1-5"}, status=400)

        try:
            task = Task.objects.get(id=task_id, supervisor=request.user)
        except Task.DoesNotExist:
            return Response({"detail": "Task not found"}, status=404)

        task.star_rating = star_rating
        task.supervisor_feedback = supervisor_feedback
        task.save(update_fields=["star_rating", "supervisor_feedback"])

        ActivityLog.objects.create(actor=request.user, action=f"Rated task {task.id} ({star_rating} stars)")
        return Response({"detail": "Saved"})


class SupervisorAttendanceView(APIView):
    permission_classes = [IsSupervisor]

    def get(self, request):
        qs = Attendance.objects.select_related("intern").filter(intern__supervisor=request.user).order_by("-created_at")[:300]
        return Response([{
            "id": a.id,
            "intern": a.intern.full_name,
            "email": a.intern.email,
            "in_office": a.in_office,
            "location_validated": a.location_validated,
            "distance_m": a.office_distance_m,
            "created_at": a.created_at.isoformat(),
        } for a in qs])


class SupervisorReportsView(APIView):
    permission_classes = [IsSupervisor]

    def get(self, request):
        qs = (
            TaskReport.objects
            .select_related("task", "intern")
            .filter(task__supervisor=request.user)
            .order_by("-created_at")[:300]
        )
        return Response([{
            "id": r.id,
            "task_id": r.task.id,
            "task_title": r.task.title,
            "intern": r.intern.email,
            "content": r.content,
            "created_at": r.created_at.isoformat(),
        } for r in qs])


class SupervisorComplaintList(APIView):
    permission_classes = [IsSupervisor]

    def get(self, request):
        qs = Complaint.objects.select_related("intern").filter(supervisor=request.user).order_by("-created_at")[:200]
        return Response([{
            "id": c.id,
            "intern": c.intern.email,
            "subject": c.subject,
            "message": c.message,
            "status": c.status,
            "created_at": c.created_at.isoformat(),
        } for c in qs])


class SupervisorComplaintUpdateStatus(APIView):
    permission_classes = [IsSupervisor]

    def post(self, request, complaint_id):
        status_val = (request.data.get("status") or "").strip()
        if status_val not in ["OPEN", "IN_REVIEW", "RESOLVED"]:
            return Response({"detail": "status must be OPEN/IN_REVIEW/RESOLVED"}, status=400)

        try:
            c = Complaint.objects.get(id=complaint_id, supervisor=request.user)
        except Complaint.DoesNotExist:
            return Response({"detail": "Complaint not found"}, status=404)

        c.status = status_val
        c.save(update_fields=["status"])

        ActivityLog.objects.create(actor=request.user, action=f"Updated complaint {c.id} -> {status_val}")
        return Response({"detail": "Updated"})
