import math
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Task, Attendance, Complaint, TaskReport, ActivityLog
from .permissions import IsIntern
from .serializers import TaskSerializer


def haversine_m(lat1, lon1, lat2, lon2):
    # meters
    R = 6371000
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    d1 = math.radians(lat2 - lat1)
    d2 = math.radians(lon2 - lon1)
    a = math.sin(d1/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(d2/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c


class InternMySupervisor(APIView):
    permission_classes = [IsIntern]

    def get(self, request):
        sup = getattr(request.user, "supervisor", None)
        if not sup:
            return Response({"detail": "No supervisor assigned"}, status=404)
        return Response({"id": sup.id, "full_name": sup.full_name, "email": sup.email})


class InternMyTasks(APIView):
    permission_classes = [IsIntern]

    def get(self, request):
        qs = Task.objects.filter(intern=request.user).select_related("intern", "supervisor").order_by("-created_at")
        return Response(TaskSerializer(qs, many=True).data)


class InternUpdateTaskStatus(APIView):
    permission_classes = [IsIntern]

    def post(self, request, task_id):
        status_val = (request.data.get("status") or "").strip()
        if status_val not in ["DONE", "IN_PROGRESS", "COMPLETED"]:
            return Response({"detail": "status must be DONE/IN_PROGRESS/COMPLETED"}, status=400)

        try:
            task = Task.objects.get(id=task_id, intern=request.user)
        except Task.DoesNotExist:
            return Response({"detail": "Task not found"}, status=404)

        task.status = status_val
        task.save(update_fields=["status"])

        ActivityLog.objects.create(actor=request.user, action=f"Updated task {task.id} -> {status_val}")
        return Response({"detail": "Updated"})


class InternSubmitTaskReport(APIView):
    permission_classes = [IsIntern]

    def post(self, request, task_id):
        content = (request.data.get("content") or "").strip()
        if not content:
            return Response({"detail": "content required"}, status=400)

        try:
            task = Task.objects.get(id=task_id, intern=request.user)
        except Task.DoesNotExist:
            return Response({"detail": "Task not found"}, status=404)

        r = TaskReport.objects.create(task=task, intern=request.user, content=content)
        ActivityLog.objects.create(actor=request.user, action=f"Submitted report for task {task.id}")
        return Response({"detail": "Report submitted", "id": r.id})


class InternMarkAttendance(APIView):
    permission_classes = [IsIntern]

    def post(self, request):
        in_office = request.data.get("in_office", False)
        lat = request.data.get("lat", None)
        lng = request.data.get("lng", None)

        # Office config from settings/.env
        office_lat = float(getattr(settings, "OFFICE_LAT", 0) or 0)
        office_lng = float(getattr(settings, "OFFICE_LNG", 0) or 0)
        radius_m = float(getattr(settings, "OFFICE_RADIUS_M", 150) or 150)

        location_validated = False
        dist = None

        if in_office in [True, "true", "True", 1, "1"]:
            # if they claim in office, try validate if lat/lng provided
            try:
                if lat is not None and lng is not None and office_lat and office_lng:
                    lat = float(lat)
                    lng = float(lng)
                    dist = haversine_m(lat, lng, office_lat, office_lng)
                    location_validated = dist <= radius_m
            except Exception:
                location_validated = False

        a = Attendance.objects.create(
            intern=request.user,
            in_office=bool(in_office in [True, "true", "True", 1, "1"]),
            lat=lat if lat is not None else None,
            lng=lng if lng is not None else None,
            location_validated=location_validated,
            office_distance_m=dist,
        )

        ActivityLog.objects.create(actor=request.user, action=f"Marked attendance (in_office={a.in_office}, validated={a.location_validated})")

        return Response({
            "id": a.id,
            "location_validated": a.location_validated,
            "office_distance_m": a.office_distance_m,
            "radius_m": radius_m,
        })


class InternComplaints(APIView):
    permission_classes = [IsIntern]

    def get(self, request):
        qs = Complaint.objects.filter(intern=request.user).order_by("-created_at")[:200]
        return Response([{
            "id": c.id,
            "subject": c.subject,
            "message": c.message,
            "status": c.status,
            "created_at": c.created_at.isoformat(),
        } for c in qs])

    def post(self, request):
        subject = (request.data.get("subject") or "").strip()
        message = (request.data.get("message") or "").strip()
        if not subject or not message:
            return Response({"detail": "subject and message required"}, status=400)

        supervisor = getattr(request.user, "supervisor", None)
        c = Complaint.objects.create(
            intern=request.user,
            supervisor=supervisor,
            subject=subject,
            message=message,
            status="OPEN",
        )

        ActivityLog.objects.create(actor=request.user, action=f"Created complaint {c.id}")
        return Response({"detail": "Sent", "id": c.id}, status=201)
