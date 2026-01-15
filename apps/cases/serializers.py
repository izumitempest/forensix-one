from rest_framework import serializers
from .models import Case, Evidence, AuditLog, CaseTag

class CaseTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseTag
        fields = '__all__'

class EvidenceSerializer(serializers.ModelSerializer):
    acquired_by_name = serializers.ReadOnlyField(source='acquired_by.username')
    
    class Meta:
        model = Evidence
        fields = '__all__'

class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user.username')
    
    class Meta:
        model = AuditLog
        fields = '__all__'

class CaseSerializer(serializers.ModelSerializer):
    created_by_name = serializers.ReadOnlyField(source='created_by.username')
    evidence_count = serializers.IntegerField(source='evidence.count', read_only=True)
    tags = CaseTagSerializer(many=True, read_only=True)
    
    class Meta:
        model = Case
        fields = '__all__'
