import csv
import io
from datetime import datetime

from django.http import HttpResponse
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

from accounts.models import User
from .models import Task, Attendance, Complaint, ActivityLog, TaskReport
from .permissions import IsAdmin


# ==============================
# ADMIN ANALYTICS
# ==============================

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


# ==============================
# ACTIVITY LOG
# ==============================

class AdminActivityLogView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        logs = ActivityLog.objects.select_related("actor").order_by("-created_at")[:200]
        return Response([
            {
                "id": log.id,
                "actor": getattr(log.actor, "email", None),
                "action": log.action,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ])


# ==============================
# ASSIGNMENT DATA
# ==============================

class AdminAssignmentsData(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        interns = User.objects.filter(role="INTERN").order_by("full_name")
        supervisors = User.objects.filter(role="SUPERVISOR").order_by("full_name")

        return Response({
            "interns": [
                {"id": i.id, "full_name": i.full_name, "email": i.email}
                for i in interns
            ],
            "supervisors": [
                {"id": s.id, "full_name": s.full_name, "email": s.email}
                for s in supervisors
            ],
        })


# ==============================
# ASSIGN INTERN
# ==============================

class AdminAssignIntern(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        intern_id = request.data.get("intern_id")
        supervisor_id = request.data.get("supervisor_id")

        if not intern_id or not supervisor_id:
            return Response({"detail": "intern_id and supervisor_id required"}, status=400)

        try:
            intern = User.objects.get(id=intern_id, role="INTERN")
            supervisor = User.objects.get(id=supervisor_id, role="SUPERVISOR")
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=404)

        intern.supervisor = supervisor
        intern.save(update_fields=["supervisor"])

        ActivityLog.objects.create(
            actor=request.user,
            action=f"Assigned {intern.email} -> {supervisor.email}"
        )

        return Response({"detail": "Assigned successfully"})


# ==============================
# UNASSIGN INTERN
# ==============================

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

        ActivityLog.objects.create(
            actor=request.user,
            action=f"Unassigned {intern.email}"
        )

        return Response({"detail": "Unassigned successfully"})


# ==============================
# ATTENDANCE
# ==============================

class AdminAttendanceView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        records = Attendance.objects.select_related("intern").order_by("-created_at")[:300]

        return Response([
            {
                "id": a.id,
                "intern": a.intern.full_name,
                "email": a.intern.email,
                "in_office": a.in_office,
                "location_validated": a.location_validated,
                "distance_m": a.office_distance_m,
                "created_at": a.created_at.isoformat(),
            }
            for a in records
        ])


# ==============================
# COMPLAINTS
# ==============================

class AdminComplaintsView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        complaints = Complaint.objects.select_related("intern", "supervisor").order_by("-created_at")[:200]

        return Response([
            {
                "id": c.id,
                "intern": c.intern.email,
                "supervisor": c.supervisor.email if c.supervisor else None,
                "subject": c.subject,
                "status": c.status,
                "created_at": c.created_at.isoformat(),
            }
            for c in complaints
        ])


# ==============================
# PROGRESS REPORT
# ==============================

class AdminProgressView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        try:
            year = int(request.query_params.get("year", timezone.now().year))
            month = int(request.query_params.get("month", timezone.now().month))
        except ValueError:
            return Response({"detail": "Invalid year or month"}, status=400)

        tasks = Task.objects.filter(created_at__year=year, created_at__month=month)
        attendance = Attendance.objects.filter(date__year=year, date__month=month)
        reports = TaskReport.objects.filter(created_at__year=year, created_at__month=month)
        complaints = Complaint.objects.filter(created_at__year=year, created_at__month=month)

        summary = {
            "tasks_created": tasks.count(),
            "tasks_completed": tasks.filter(status="COMPLETED").count(),
            "attendance_marked": attendance.count(),
            "reports_submitted": reports.count(),
            "complaints": complaints.count(),
        }

        rows = []
        interns = User.objects.filter(role="INTERN")

        for intern in interns:
            rows.append({
                "intern": intern.full_name,
                "email": intern.email,
                "tasks_created": tasks.filter(intern=intern).count(),
                "tasks_completed": tasks.filter(intern=intern, status="COMPLETED").count(),
                "attendance": attendance.filter(intern=intern).count(),
                "reports": reports.filter(intern=intern).count(),
                "complaints": complaints.filter(intern=intern).count(),
            })

        return Response({
            "summary": summary,
            "rows": rows
        })


# ==============================
# MONTHLY CSV EXPORT
# ==============================

class AdminMonthlyReportCSV(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        year = int(request.query_params.get("year", timezone.now().year))
        month = int(request.query_params.get("month", timezone.now().month))

        tasks = Task.objects.filter(
            created_at__year=year,
            created_at__month=month
        ).select_related("intern", "supervisor")

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="monthly_report_{year}_{month:02d}.csv"'

        writer = csv.writer(response)
        writer.writerow([
            "Task ID", "Title", "Status",
            "Intern", "Supervisor",
            "Rating", "Feedback", "Created At"
        ])

        for t in tasks:
            writer.writerow([
                t.id,
                t.title,
                t.status,
                t.intern.full_name if t.intern else "",
                t.supervisor.full_name if t.supervisor else "",
                t.star_rating,
                (t.supervisor_feedback or "").replace("\n", " "),
                t.created_at,
            ])

        return response


# ==============================
# MONTHLY PDF EXPORT
# ==============================

class AdminMonthlyReportPDF(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        year = int(request.query_params.get("year", timezone.now().year))
        month = int(request.query_params.get("month", timezone.now().month))

        tasks = Task.objects.filter(
            created_at__year=year,
            created_at__month=month
        ).select_related("intern", "supervisor")

        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        y = height - 50
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, y, f"Monthly Report - {year}-{month:02d}")

        y -= 30
        pdf.setFont("Helvetica", 10)

        for t in tasks:
            if y < 50:
                pdf.showPage()
                pdf.setFont("Helvetica", 10)
                y = height - 50

            line = f"#{t.id} | {t.title} | {t.status} | {t.intern.full_name if t.intern else ''}"
            pdf.drawString(50, y, line[:100])
            y -= 15

        pdf.save()
        buffer.seek(0)

        response = HttpResponse(buffer, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="monthly_report_{year}_{month:02d}.pdf"'
        return response