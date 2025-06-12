# serializers.py
from rest_framework import serializers
from .models import ServiceShift

class ServiceShiftSerializer(serializers.ModelSerializer):
    from_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M", input_formats=["%Y-%m-%d %H:%M"])
    to_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M", input_formats=["%Y-%m-%d %H:%M"])

    class Meta:
        model = ServiceShift
        fields = '__all__'
        read_only_fields = ['admin', 'shift_duration']
