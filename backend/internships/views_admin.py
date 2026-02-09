import calendar
from datetime import datetime

from django.http import HttpResponse
from django.utils.timezone import make_aware
from rest_framework.views import APIView
from rest_framework.response import Response

from accounts.models import User
from .models import Task, Attendance, Complaint, ActivityLog
from .permissions import IsAdmin
from .serializers import TaskSerializer


class AdminAnalyticsView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        return Response({
            "counts": {
                "interns": User.objects.filter(role="INTERN").count(),
                "supervisors": User.objects.filter(role="SUPERVISOR").count(),
                "tasks_total": Task.objects.count(),
                "complaints_open": Complaint.objects.filter(status="OPEN").count(),
            }
        })


class AdminActivityLogView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        logs = ActivityLog.objects.select_related("actor").order_by("-created_at")[:200]
        return Response([{
            "id": l.id,
            "actor": getattr(l.actor, "email", None),
            "action": l.action,
            "created_at": l.created_at.isoformat(),
        } for l in logs])


class AdminAssignmentsData(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        interns = User.objects.filter(role="INTERN").order_by("full_name")
        supervisors = User.objects.filter(role="SUPERVISOR").order_by("full_name")
        return Response({
            "interns": [{"id": i.id, "full_name": i.full_name, "email": i.email} for i in interns],
            "supervisors": [{"id": s.id, "full_name": s.full_name, "email": s.email} for s in supervisors],
        })


class AdminAssignIntern(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        intern_id = request.data.get("intern_id")
        supervisor_id = request.data.get("supervisor_id")

        if not intern_id or not supervisor_id:
            return Response({"detail": "intern_id and supervisor_id required"}, status=400)

        try:
            intern = User.objects.get(id=intern_id, role="INTERN")
        except User.DoesNotExist:
            return Response({"detail": "Intern not found"}, status=404)

        try:
            supervisor = User.objects.get(id=supervisor_id, role="SUPERVISOR")
        except User.DoesNotExist:
            return Response({"detail": "Supervisor not found"}, status=404)

        intern.supervisor = supervisor
        intern.save(update_fields=["supervisor"])

        ActivityLog.objects.create(actor=request.user, action=f"Assigned {intern.email} -> {supervisor.email}")
        return Response({"detail": "Assigned"})


class AdminUnassignIntern(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        intern_id = request.data.get("intern_id")
        if not intern_id:
            return Response({"detail": "intern_id required"}, status=400)

        try:
            intern = User.objects.get(id=intern_id, role="INTERN")
        except User.DoesNotExist:
            return Response({"detail": "Intern not found"}, status=404)

        intern.supervisor = None
        intern.save(update_fields=["supervisor"])

        ActivityLog.objects.create(actor=request.user, action=f"Unassigned {intern.email}")
        return Response({"detail": "Unassigned"})


class AdminAttendanceView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = Attendance.objects.select_related("intern").order_by("-created_at")[:300]
        return Response([{
            "id": a.id,
            "intern": a.intern.full_name,
            "email": a.intern.email,
            "in_office": a.in_office,
            "location_validated": a.location_validated,
            "distance_m": a.office_distance_m,
            "created_at": a.created_at.isoformat(),
        } for a in qs])


class AdminComplaintsView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = Complaint.objects.select_related("intern", "supervisor").order_by("-created_at")[:200]
        return Response([{
            "id": c.id,
            "intern": c.intern.email,
            "supervisor": c.supervisor.email if c.supervisor else None,
            "subject": c.subject,
            "status": c.status,
            "created_at": c.created_at.isoformat(),
        } for c in qs])


class AdminProgressView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = Task.objects.select_related("intern", "supervisor").order_by("-created_at")[:300]
        return Response(TaskSerializer(qs, many=True).data)


def _month_range(year: int, month: int):
    last_day = calendar.monthrange(year, month)[1]
    start = make_aware(datetime(year, month, 1, 0, 0, 0))
    end = make_aware(datetime(year, month, last_day, 23, 59, 59))
    return start, end


class AdminMonthlyReportCSV(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        try:
            year = int(request.query_params.get("year"))
            month = int(request.query_params.get("month"))
        except (TypeError, ValueError):
            return Response({"detail": "year and month query params required"}, status=400)

        start, end = _month_range(year, month)
        tasks = (
            Task.objects.select_related("intern", "supervisor")
            .filter(created_at__range=(start, end))
            .order_by("created_at")
        )

        # safe CSV (basic)
        lines = ["task_id,intern_email,supervisor_email,title,status,star_rating,created_at"]
        for t in tasks:
            title = (t.title or "").replace('"', "'")
            title = f'"{title}"'  # quote title to avoid comma issues
            lines.append(
                f"{t.id},{t.intern.email},{t.supervisor.email},{title},{t.status},{t.star_rating or ''},{t.created_at.isoformat()}"
            )

        resp = HttpResponse("\n".join(lines), content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = f'attachment; filename="monthly_report_{year}_{month}.csv"'
        return resp


class AdminMonthlyReportPDF(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        year = request.query_params.get("year")
        month = request.query_params.get("month")
        content = f"Monthly report PDF placeholder - {year}-{month}\nUse CSV export for now."
        resp = HttpResponse(content.encode("utf-8"), content_type="application/pdf")
        resp["Content-Disposition"] = f'attachment; filename="monthly_report_{year}_{month}.pdf"'
        return resp
