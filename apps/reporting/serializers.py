from rest_framework import serializers
from .models import Report, ReportTemplate

class ReportTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportTemplate
        fields = '__all__'

class ReportSerializer(serializers.ModelSerializer):
    template_name = serializers.ReadOnlyField(source='template.name')
    created_by_name = serializers.ReadOnlyField(source='created_by.username')
    
    class Meta:
        model = Report
        fields = '__all__'
