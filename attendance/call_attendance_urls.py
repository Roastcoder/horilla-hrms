"""
Call-based Auto Attendance URLs

URL patterns for call attendance management system.
"""

from django.urls import path
from . import call_attendance_views

app_name = 'call_attendance'

urlpatterns = [
    # Dashboard
    path('call-attendance/', call_attendance_views.call_attendance_dashboard, name='dashboard'),
    
    # Call Logs
    path('call-logs/', call_attendance_views.call_log_list, name='call_log_list'),
    path('call-logs/create/', call_attendance_views.call_log_create, name='call_log_create'),
    path('call-logs/<int:pk>/edit/', call_attendance_views.call_log_edit, name='call_log_edit'),
    path('call-logs/bulk-upload/', call_attendance_views.call_log_bulk_upload, name='call_log_bulk_upload'),
    
    # Configuration
    path('config/', call_attendance_views.attendance_config, name='attendance_config'),
    
    # Attendance Management
    path('attendances/', call_attendance_views.attendance_list, name='attendance_list'),
    path('attendances/manual-update/', call_attendance_views.manual_update_attendance, name='manual_update_attendance'),
    path('attendances/download-template/', call_attendance_views.download_attendance_template, name='download_attendance_template'),
    path('attendances/upload-bulk/', call_attendance_views.upload_bulk_attendance, name='upload_bulk_attendance'),
    path('attendances/calculate/', call_attendance_views.calculate_attendance, name='calculate_attendance'),
    
    # Employee View
    path('my-attendance/', call_attendance_views.employee_attendance_view, name='employee_attendance_view'),
    
    # Audit & Reports
    path('audit-trail/', call_attendance_views.audit_trail, name='audit_trail'),
    path('report/', call_attendance_views.attendance_report, name='attendance_report'),
]