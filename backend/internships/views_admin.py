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
        year = int(request.query_params.get("year", timezone.now().year))
        month = int(request.query_params.get("month", timezone.now().month))

        # Filter month data
        tasks = Task.objects.filter(created_at__year=year, created_at__month=month)
        attendance = Attendance.objects.filter(date__year=year, date__month=month)
        reports = TaskReport.objects.filter(created_at__year=year, created_at__month=month)
        complaints = Complaint.objects.filter(created_at__year=year, created_at__month=month)

        # -------- SUMMARY --------
        summary = {
            "tasks_created": tasks.count(),
            "tasks_completed": tasks.filter(status="COMPLETED").count(),
            "attendance_marked": attendance.count(),
            "reports_submitted": reports.count(),
            "complaints": complaints.count(),
        }

        # -------- PER INTERN TABLE --------
        interns = User.objects.filter(role="INTERN")

        rows = []
        for intern in interns:
            t = tasks.filter(intern=intern)
            a = attendance.filter(intern=intern)
            r = reports.filter(intern=intern)
            c = complaints.filter(intern=intern)

            rows.append({
                "intern": intern.full_name,
                "email": intern.email,
                "tasks_created": t.count(),
                "tasks_completed": t.filter(status="COMPLETED").count(),
                "attendance": a.count(),
                "reports": r.count(),
                "complaints": c.count(),
            })

        return Response({
            "summary": summary,
            "rows": rows
        })


# internships/views_admin.py

class AdminMonthlyReportCSV(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        year = int(request.query_params.get("year", timezone.now().year))
        month = int(request.query_params.get("month", timezone.now().month))

        qs = Task.objects.filter(created_at__year=year, created_at__month=month).select_related("intern", "supervisor")

        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="monthly_report_{year}_{month:02d}.csv"'

        writer = csv.writer(response)
        writer.writerow([
            "Task ID", "Title", "Status",
            "Intern Name", "Intern Email",
            "Supervisor Name", "Supervisor Email",
            "Star Rating", "Supervisor Feedback",
            "Created At"
        ])

        for t in qs:
            writer.writerow([
                t.id,
                getattr(t, "title", "") or "",
                getattr(t, "status", "") or "",
                getattr(getattr(t, "intern", None), "full_name", "") or "",
                getattr(getattr(t, "intern", None), "email", "") or "",
                getattr(getattr(t, "supervisor", None), "full_name", "") or "",
                getattr(getattr(t, "supervisor", None), "email", "") or "",
                getattr(t, "star_rating", "") or "",
                (getattr(t, "supervisor_feedback", "") or "").replace("\n", " ").strip(),
                getattr(t, "created_at", "") or "",
            ])

        return response


class AdminMonthlyReportPDF(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        year = int(request.query_params.get("year", timezone.now().year))
        month = int(request.query_params.get("month", timezone.now().month))

        qs = Task.objects.filter(created_at__year=year, created_at__month=month).select_related("intern", "supervisor")

        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        y = height - 50
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y, f"Admin Monthly Report - {year}-{month:02d}")

        y -= 20
        p.setFont("Helvetica", 10)
        p.drawString(50, y, f"Total Tasks: {qs.count()}")

        y -= 20
        p.setFont("Helvetica-Bold", 10)
        p.drawString(50, y, "Task")
        p.drawString(270, y, "Intern")
        p.drawString(460, y, "Status")
        y -= 8
        p.line(50, y, 550, y)
        y -= 16

        p.setFont("Helvetica", 9)
        for t in qs:
            if y < 70:
                p.showPage()
                y = height - 50

            title = (getattr(t, "title", "") or "")[:30]
            intern = (getattr(getattr(t, "intern", None), "full_name", "") or "")[:22]
            status_txt = (getattr(t, "status", "") or "")[:12]

            p.drawString(50, y, f"#{t.id} {title}")
            p.drawString(270, y, intern)
            p.drawString(460, y, status_txt)
            y -= 14

        p.showPage()
        p.save()

        buffer.seek(0)
        resp = HttpResponse(buffer.getvalue(), content_type="application/pdf")
        resp["Content-Disposition"] = f'attachment; filename="monthly_report_{year}_{month:02d}.pdf"'
        return resp