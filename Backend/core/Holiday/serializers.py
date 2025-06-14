from rest_framework import serializers
from .models import Holiday

class HolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Holiday
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class HolidayUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Holiday
        fields = '__all__'
        read_only_fields = ['id', 'admin', 'organization', 'created_at', 'updated_at']