"""
URL patterns for Employee Permission Assignment

Add these URLs to your main urls.py or include them in your employee app URLs.
"""

from django.urls import path
from employee_permission_views import (
    employee_permission_assignment_view,
    get_employee_permissions,
    assign_employee_permissions,
    remove_employee_permissions,
    bulk_assign_employee_permissions
)

# Employee Permission Assignment URLs
employee_permission_urlpatterns = [
    # Main permission assignment interface
    path(
        'employee-permission-assignment/',
        employee_permission_assignment_view,
        name='employee-permission-assignment'
    ),
    
    # Get current permissions for an employee (AJAX)
    path(
        'employee-permissions/<int:employee_id>/',
        get_employee_permissions,
        name='get-employee-permissions'
    ),
    
    # Assign permissions to an employee (AJAX)
    path(
        'assign-employee-permissions/',
        assign_employee_permissions,
        name='assign-employee-permissions'
    ),
    
    # Remove permissions from an employee (AJAX)
    path(
        'remove-employee-permissions/',
        remove_employee_permissions,
        name='remove-employee-permissions'
    ),
    
    # Bulk assign permissions to multiple employees (AJAX)
    path(
        'bulk-assign-employee-permissions/',
        bulk_assign_employee_permissions,
        name='bulk-assign-employee-permissions'
    ),
]

# To integrate with existing Horilla URLs, add these to your main urls.py:
"""
# In horilla/urls.py or your main URL configuration:

from django.urls import path, include
from employee_permission_views import (
    employee_permission_assignment_view,
    get_employee_permissions,
    assign_employee_permissions,
    remove_employee_permissions,
    bulk_assign_employee_permissions
)

urlpatterns = [
    # ... existing patterns ...
    
    # Employee Permission Assignment
    path('employee-permission-assignment/', employee_permission_assignment_view, name='employee-permission-assignment'),
    path('employee-permissions/<int:employee_id>/', get_employee_permissions, name='get-employee-permissions'),
    path('assign-employee-permissions/', assign_employee_permissions, name='assign-employee-permissions'),
    path('remove-employee-permissions/', remove_employee_permissions, name='remove-employee-permissions'),
    path('bulk-assign-employee-permissions/', bulk_assign_employee_permissions, name='bulk-assign-employee-permissions'),
    
    # ... rest of your patterns ...
]
"""