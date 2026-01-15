from rest_framework import serializers
from .models import AcquisitionTask

class AcquisitionTaskSerializer(serializers.ModelSerializer):
    created_by_name = serializers.ReadOnlyField(source='created_by.username')
    
    class Meta:
        model = AcquisitionTask
        fields = '__all__'
