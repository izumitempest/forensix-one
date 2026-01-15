from django.contrib import admin
from .models import Role, CaseParticipant, CaseNote

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'can_acquire', 'can_analyze', 'can_view_reports')

@admin.register(CaseParticipant)
class CaseParticipantAdmin(admin.ModelAdmin):
    list_display = ('user', 'case', 'role', 'is_active')
    list_filter = ('case', 'role', 'is_active')

@admin.register(CaseNote)
class CaseNoteAdmin(admin.ModelAdmin):
    list_display = ('author', 'case', 'created_at')
    list_filter = ('case', 'author')
    search_fields = ('content',)
    readonly_fields = ('created_at', 'updated_at')
