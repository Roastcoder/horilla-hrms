"""
Employee Permission Assignment Views

Simple views for managing employee permissions in Horilla HRMS.
These views integrate with the existing permission system.
"""

import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Permission
from django.db import transaction
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.apps import apps

from employee.models import Employee


@login_required
@permission_required('auth.change_permission')
def employee_permission_assignment_view(request):
    """
    Main view for employee permission assignment interface.
    """
    # Get all active employees
    employees = Employee.objects.filter(is_active=True).select_related('employee_user_id')
    
    # Get all permissions grouped by app
    permissions = Permission.objects.all().select_related('content_type')
    permissions_by_app = {}
    
    for perm in permissions:
        app_label = perm.content_type.app_label
        if app_label not in permissions_by_app:
            permissions_by_app[app_label] = []
        permissions_by_app[app_label].append(perm)
    
    context = {
        'employees': employees,
        'permissions_by_app': permissions_by_app,
    }
    
    return render(request, 'employee/permission_assignment.html', context)


@login_required
@permission_required('auth.view_permission')
def get_employee_permissions(request, employee_id):
    """
    Get current permissions for a specific employee.
    Returns JSON response with direct and group permissions.
    """
    try:
        employee = get_object_or_404(Employee, id=employee_id, is_active=True)
        user = employee.employee_user_id
        
        if not user:
            return JsonResponse({'error': 'Employee has no associated user account'}, status=400)
        
        # Get direct permissions
        user_permissions = user.user_permissions.all().select_related('content_type')
        direct_permissions = [
            {
                'id': perm.id,
                'codename': perm.codename,
                'name': perm.name,
                'app_label': perm.content_type.app_label
            }
            for perm in user_permissions
        ]
        
        # Get group permissions
        group_permissions_qs = Permission.objects.filter(group__user=user).select_related('content_type')
        group_permissions = []
        
        for perm in group_permissions_qs:
            groups = user.groups.filter(permissions=perm)
            group_names = [g.name for g in groups]
            group_permissions.append({
                'id': perm.id,
                'codename': perm.codename,
                'name': perm.name,
                'app_label': perm.content_type.app_label,
                'groups': ', '.join(group_names)
            })
        
        return JsonResponse({
            'success': True,
            'permissions': direct_permissions,
            'group_permissions': group_permissions,
            'employee_name': f"{employee.employee_first_name} {employee.employee_last_name}"
        })
        
    except Employee.DoesNotExist:
        return JsonResponse({'error': 'Employee not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@permission_required('auth.change_permission')
@require_http_methods(['POST'])
@transaction.atomic
def assign_employee_permissions(request):
    """
    Assign permissions to an employee.
    Handles both adding and replacing permissions.
    """
    try:
        employee_id = request.POST.get('employee_id')
        permissions_json = request.POST.get('permissions')
        mode = request.POST.get('mode', 'add')  # 'add' or 'replace'
        
        if not employee_id or not permissions_json:
            return JsonResponse({'success': False, 'message': 'Missing required parameters'})
        
        # Parse permissions
        try:
            permission_codenames = json.loads(permissions_json)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid permissions format'})
        
        # Get employee and user
        employee = get_object_or_404(Employee, id=employee_id, is_active=True)
        user = employee.employee_user_id
        
        if not user:
            return JsonResponse({'success': False, 'message': 'Employee has no associated user account'})
        
        # Get permission objects
        permissions = Permission.objects.filter(codename__in=permission_codenames)
        found_codenames = set(permissions.values_list('codename', flat=True))
        missing_codenames = set(permission_codenames) - found_codenames
        
        if missing_codenames:
            return JsonResponse({
                'success': False, 
                'message': f'Permissions not found: {", ".join(missing_codenames)}'
            })
        
        if not permissions:
            return JsonResponse({'success': False, 'message': 'No valid permissions found'})
        
        # Assign permissions
        if mode == 'replace':
            user.user_permissions.clear()
            user.user_permissions.set(permissions)
            action = 'replaced with'
        else:
            user.user_permissions.add(*permissions)
            action = 'added'
        
        message = f'{len(permissions)} permissions {action} for {employee.employee_first_name} {employee.employee_last_name}'
        
        return JsonResponse({
            'success': True,
            'message': message,
            'assigned_permissions': [
                {'codename': perm.codename, 'name': perm.name}
                for perm in permissions
            ]
        })
        
    except Employee.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Employee not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})


@login_required
@permission_required('auth.change_permission')
@require_http_methods(['POST'])
@transaction.atomic
def remove_employee_permissions(request):
    """
    Remove specific permissions from an employee.
    """
    try:
        employee_id = request.POST.get('employee_id')
        permissions_json = request.POST.get('permissions')
        
        if not employee_id or not permissions_json:
            return JsonResponse({'success': False, 'message': 'Missing required parameters'})
        
        # Parse permissions
        try:
            permission_codenames = json.loads(permissions_json)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid permissions format'})
        
        # Get employee and user
        employee = get_object_or_404(Employee, id=employee_id, is_active=True)
        user = employee.employee_user_id
        
        if not user:
            return JsonResponse({'success': False, 'message': 'Employee has no associated user account'})
        
        # Get permission objects
        permissions = Permission.objects.filter(codename__in=permission_codenames)
        
        if not permissions:
            return JsonResponse({'success': False, 'message': 'No valid permissions found to remove'})
        
        # Remove permissions
        user.user_permissions.remove(*permissions)
        
        message = f'{len(permissions)} permissions removed from {employee.employee_first_name} {employee.employee_last_name}'
        
        return JsonResponse({
            'success': True,
            'message': message,
            'removed_permissions': [
                {'codename': perm.codename, 'name': perm.name}
                for perm in permissions
            ]
        })
        
    except Employee.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Employee not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})


@login_required
@permission_required('auth.change_permission')
@require_http_methods(['POST'])
@transaction.atomic
def bulk_assign_employee_permissions(request):
    """
    Assign permissions to multiple employees at once.
    """
    try:
        employee_ids_json = request.POST.get('employee_ids')
        permissions_json = request.POST.get('permissions')
        mode = request.POST.get('mode', 'add')
        
        if not employee_ids_json or not permissions_json:
            return JsonResponse({'success': False, 'message': 'Missing required parameters'})
        
        # Parse data
        try:
            employee_ids = json.loads(employee_ids_json)
            permission_codenames = json.loads(permissions_json)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON format'})
        
        # Get employees and permissions
        employees = Employee.objects.filter(id__in=employee_ids, is_active=True).select_related('employee_user_id')
        permissions = Permission.objects.filter(codename__in=permission_codenames)
        
        if not employees:
            return JsonResponse({'success': False, 'message': 'No valid employees found'})
        
        if not permissions:
            return JsonResponse({'success': False, 'message': 'No valid permissions found'})
        
        # Process each employee
        success_count = 0
        errors = []
        
        for employee in employees:
            try:
                user = employee.employee_user_id
                if not user:
                    errors.append(f'{employee.employee_first_name} {employee.employee_last_name}: No user account')
                    continue
                
                if mode == 'replace':
                    user.user_permissions.clear()
                    user.user_permissions.set(permissions)
                else:
                    user.user_permissions.add(*permissions)
                
                success_count += 1
                
            except Exception as e:
                errors.append(f'{employee.employee_first_name} {employee.employee_last_name}: {str(e)}')
        
        message = f'Successfully processed {success_count}/{len(employees)} employees'
        if errors:
            message += f'. Errors: {"; ".join(errors[:3])}'  # Show first 3 errors
        
        return JsonResponse({
            'success': True,
            'message': message,
            'success_count': success_count,
            'total_count': len(employees),
            'errors': errors
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})