from rest_framework import serializers
from .models import Task

class TaskSerializer(serializers.ModelSerializer):
    intern_name = serializers.CharField(source="intern.full_name", read_only=True)
    supervisor_name = serializers.CharField(source="supervisor.full_name", read_only=True)
    intern_email = serializers.CharField(source="intern.email", read_only=True)

    class Meta:
        model = Task
        fields = "__all__"

class TaskCreateSerializer(serializers.Serializer):
    intern = serializers.IntegerField()
    title = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True)

class TaskStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["DONE","IN_PROGRESS","COMPLETED"])

class TaskRateSerializer(serializers.Serializer):
    star_rating = serializers.IntegerField(min_value=1, max_value=5)
    supervisor_feedback = serializers.CharField(required=False, allow_blank=True)

class TaskReportSerializer(serializers.Serializer):
    content = serializers.CharField()

class AttendanceMarkSerializer(serializers.Serializer):
    in_office = serializers.BooleanField()
    lat = serializers.FloatField(required=False)
    lng = serializers.FloatField(required=False)

class ComplaintCreateSerializer(serializers.Serializer):
    subject = serializers.CharField()
    message = serializers.CharField()

class ComplaintStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["OPEN","IN_REVIEW","RESOLVED"])
