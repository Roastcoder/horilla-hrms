"""
Call Attendance Admin Configuration

Admin interface for managing call logs, attendance configuration, and audit trails.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .call_attendance_models import (
    CallLog, CallAttendanceConfig, CallAttendance, CallAttendanceAudit
)


@admin.register(CallLog)
class CallLogAdmin(admin.ModelAdmin):
    list_display = [
        'employee_id', 'call_date', 'call_duration_minutes', 
        'call_count', 'source', 'created_at'
    ]
    list_filter = ['call_date', 'source', 'created_at']
    search_fields = [
        'employee_id__employee_first_name', 
        'employee_id__employee_last_name'
    ]
    date_hierarchy = 'call_date'
    ordering = ['-call_date', 'employee_id']
    
    fieldsets = (
        (_('Call Information'), {
            'fields': ('employee_id', 'call_date', 'call_duration_minutes', 'call_count')
        }),
        (_('Metadata'), {
            'fields': ('source',),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing existing object
            return ['created_at', 'updated_at']
        return []


@admin.register(CallAttendanceConfig)
class CallAttendanceConfigAdmin(admin.ModelAdmin):
    list_display = [
        'full_day_minutes', 'half_day_minutes', 
        'absent_threshold_minutes', 'is_active'
    ]
    list_filter = ['is_active']
    
    fieldsets = (
        (_('Attendance Thresholds'), {
            'fields': (
                'full_day_minutes', 'half_day_minutes', 
                'absent_threshold_minutes'
            ),
            'description': _('Configure call duration thresholds for attendance calculation')
        }),
        (_('Status'), {
            'fields': ('is_active',)
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one active configuration
        if CallAttendanceConfig.objects.filter(is_active=True).exists():
            return False
        return super().has_add_permission(request)


@admin.register(CallAttendance)
class CallAttendanceAdmin(admin.ModelAdmin):
    list_display = [
        'employee_id', 'attendance_date', 'call_duration_minutes',
        'attendance_status_badge', 'source_badge', 'updated_by'
    ]
    list_filter = [
        'attendance_date', 'attendance_status', 'source', 
        'updated_by', 'created_at'
    ]
    search_fields = [
        'employee_id__employee_first_name', 
        'employee_id__employee_last_name'
    ]
    date_hierarchy = 'attendance_date'
    ordering = ['-attendance_date', 'employee_id']
    
    fieldsets = (
        (_('Employee & Date'), {
            'fields': ('employee_id', 'attendance_date')
        }),
        (_('Call Data'), {
            'fields': ('call_duration_minutes', 'call_count')
        }),
        (_('Attendance Status'), {
            'fields': ('attendance_status', 'source')
        }),
        (_('Manual Update Info'), {
            'fields': ('manual_reason', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def attendance_status_badge(self, obj):
        colors = {
            'PRESENT': 'green',
            'HALF_DAY': 'orange', 
            'ABSENT': 'red'
        }
        color = colors.get(obj.attendance_status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_attendance_status_display()
        )
    attendance_status_badge.short_description = _('Status')
    
    def source_badge(self, obj):
        colors = {
            'AUTO': 'blue',
            'MANUAL': 'purple'
        }
        color = colors.get(obj.source, 'gray')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_source_display()
        )
    source_badge.short_description = _('Source')
    
    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj and obj.source == 'AUTO':
            # Make auto-calculated records mostly readonly
            readonly.extend(['call_duration_minutes', 'call_count', 'attendance_status'])
        return readonly


@admin.register(CallAttendanceAudit)
class CallAttendanceAuditAdmin(admin.ModelAdmin):
    list_display = [
        'employee_id', 'attendance_date', 'updated_by',
        'old_status', 'new_status', 'timestamp'
    ]
    list_filter = [
        'attendance_date', 'updated_by', 'timestamp',
        'old_status', 'new_status'
    ]
    search_fields = [
        'employee_id__employee_first_name',
        'employee_id__employee_last_name',
        'updated_by__employee_first_name',
        'updated_by__employee_last_name'
    ]
    date_hierarchy = 'attendance_date'
    ordering = ['-timestamp']
    
    fieldsets = (
        (_('Audit Information'), {
            'fields': ('employee_id', 'attendance_date', 'updated_by', 'timestamp')
        }),
        (_('Changes Made'), {
            'fields': (
                ('old_call_duration', 'new_call_duration'),
                ('old_call_count', 'new_call_count'),
                ('old_status', 'new_status'),
                'reason'
            )
        }),
    )
    
    readonly_fields = [
        'call_attendance', 'employee_id', 'attendance_date',
        'old_call_duration', 'old_call_count', 'old_status',
        'new_call_duration', 'new_call_count', 'new_status',
        'reason', 'updated_by', 'timestamp'
    ]
    
    def has_add_permission(self, request):
        return False  # Audit records should only be created programmatically
    
    def has_change_permission(self, request, obj=None):
        return False  # Audit records should be immutable
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser  # Only superusers can delete audit records


# Custom admin actions
def recalculate_attendance_status(modeladmin, request, queryset):
    """Admin action to recalculate attendance status based on current config"""
    from .call_attendance_services import CallAttendanceService
    
    config = CallAttendanceService.get_active_config()
    if not config:
        modeladmin.message_user(request, _("No active configuration found"), level='ERROR')
        return
    
    updated_count = 0
    for attendance in queryset.filter(source='AUTO'):
        new_status = CallAttendanceService.calculate_attendance_status(
            attendance.call_duration_minutes, config
        )
        if new_status != attendance.attendance_status:
            attendance.attendance_status = new_status
            attendance.save()
            updated_count += 1
    
    modeladmin.message_user(
        request, 
        _("Updated {} attendance records").format(updated_count)
    )

recalculate_attendance_status.short_description = _("Recalculate attendance status")

# Add the action to CallAttendanceAdmin
CallAttendanceAdmin.actions = [recalculate_attendance_status]