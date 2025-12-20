"""
Call Attendance API URLs

URL patterns for call attendance REST API endpoints.
"""

from django.urls import path
from . import call_attendance_api

app_name = 'call_attendance_api'

urlpatterns = [
    # API Documentation
    path('api/docs/', call_attendance_api.api_documentation, name='api_documentation'),
    
    # Call Logs API
    path('api/call-logs/create/', call_attendance_api.api_create_call_log, name='api_create_call_log'),
    path('api/call-logs/bulk-create/', call_attendance_api.api_bulk_create_call_logs, name='api_bulk_create_call_logs'),
    path('api/call-logs/', call_attendance_api.api_get_call_logs, name='api_get_call_logs'),
    
    # Attendance API
    path('api/attendance/calculate/', call_attendance_api.api_calculate_attendance, name='api_calculate_attendance'),
    path('api/attendance/summary/', call_attendance_api.api_get_attendance_summary, name='api_get_attendance_summary'),
]