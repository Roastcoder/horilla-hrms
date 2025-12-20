"""
Call Attendance API

REST API endpoints for external call data integration.
Platform-agnostic API for receiving call logs from any system.
"""

import json
from datetime import datetime, date
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.utils.decorators import method_decorator
from django.views import View

from employee.models import Employee
from .call_attendance_services import CallLogService, CallAttendanceService
from .call_attendance_models import CallLog


@csrf_exempt
@require_http_methods(["POST"])
def api_create_call_log(request):
    """
    API endpoint to create call log entries
    
    Expected JSON payload:
    {
        "employee_id": 123,
        "call_date": "2024-01-15",
        "call_duration_minutes": 180,
        "call_count": 25,
        "source": "API_SYSTEM_NAME"
    }
    """
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['employee_id', 'call_date', 'call_duration_minutes']
        for field in required_fields:
            if field not in data:
                return JsonResponse({
                    'error': f'Missing required field: {field}'
                }, status=400)
        
        # Validate employee exists
        try:
            employee = Employee.objects.get(id=data['employee_id'])
        except Employee.DoesNotExist:
            return JsonResponse({
                'error': f'Employee with ID {data["employee_id"]} not found'
            }, status=404)
        
        # Parse date
        try:
            call_date = datetime.strptime(data['call_date'], '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({
                'error': 'Invalid date format. Use YYYY-MM-DD'
            }, status=400)
        
        # Validate call duration
        call_duration = data['call_duration_minutes']
        if not isinstance(call_duration, int) or call_duration < 0:
            return JsonResponse({
                'error': 'call_duration_minutes must be a non-negative integer'
            }, status=400)
        
        # Create call log
        call_log = CallLogService.create_call_log(
            employee=employee,
            call_date=call_date,
            call_duration_minutes=call_duration,
            call_count=data.get('call_count', 0),
            source=data.get('source', 'API')
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Call log created successfully',
            'data': {
                'id': call_log.id,
                'employee_id': call_log.employee_id.id,
                'call_date': call_log.call_date.strftime('%Y-%m-%d'),
                'call_duration_minutes': call_log.call_duration_minutes,
                'call_count': call_log.call_count,
                'source': call_log.source
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON payload'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': f'Internal server error: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_bulk_create_call_logs(request):
    """
    API endpoint to bulk create call log entries
    
    Expected JSON payload:
    {
        "call_logs": [
            {
                "employee_id": 123,
                "call_date": "2024-01-15",
                "call_duration_minutes": 180,
                "call_count": 25
            },
            ...
        ],
        "source": "API_SYSTEM_NAME"
    }
    """
    try:
        data = json.loads(request.body)
        
        if 'call_logs' not in data or not isinstance(data['call_logs'], list):
            return JsonResponse({
                'error': 'call_logs must be a list'
            }, status=400)
        
        call_logs_data = []
        errors = []
        
        for i, log_data in enumerate(data['call_logs']):
            try:
                # Validate required fields
                required_fields = ['employee_id', 'call_date', 'call_duration_minutes']
                for field in required_fields:
                    if field not in log_data:
                        errors.append(f'Row {i+1}: Missing required field: {field}')
                        continue
                
                # Parse and validate data
                call_date = datetime.strptime(log_data['call_date'], '%Y-%m-%d').date()
                
                call_logs_data.append({
                    'employee_id': log_data['employee_id'],
                    'call_date': call_date,
                    'call_duration_minutes': log_data['call_duration_minutes'],
                    'call_count': log_data.get('call_count', 0),
                    'source': data.get('source', 'BULK_API')
                })
                
            except (ValueError, KeyError) as e:
                errors.append(f'Row {i+1}: {str(e)}')
        
        if errors:
            return JsonResponse({
                'error': 'Validation errors',
                'details': errors
            }, status=400)
        
        # Bulk create call logs
        created, updated = CallLogService.bulk_create_call_logs(call_logs_data)
        
        return JsonResponse({
            'success': True,
            'message': f'Bulk operation completed',
            'data': {
                'created': created,
                'updated': updated,
                'total_processed': len(call_logs_data)
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON payload'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': f'Internal server error: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
def api_get_call_logs(request):
    """
    API endpoint to retrieve call logs
    
    Query parameters:
    - employee_id: Filter by employee ID
    - date_from: Start date (YYYY-MM-DD)
    - date_to: End date (YYYY-MM-DD)
    - limit: Number of records to return (default: 100)
    """
    try:
        # Get query parameters
        employee_id = request.GET.get('employee_id')
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        limit = int(request.GET.get('limit', 100))
        
        # Build query
        queryset = CallLog.objects.select_related('employee_id')
        
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        
        if date_from:
            date_from_parsed = datetime.strptime(date_from, '%Y-%m-%d').date()
            queryset = queryset.filter(call_date__gte=date_from_parsed)
        
        if date_to:
            date_to_parsed = datetime.strptime(date_to, '%Y-%m-%d').date()
            queryset = queryset.filter(call_date__lte=date_to_parsed)
        
        # Apply limit and order
        call_logs = queryset.order_by('-call_date', '-created_at')[:limit]
        
        # Serialize data
        data = []
        for log in call_logs:
            data.append({
                'id': log.id,
                'employee_id': log.employee_id.id,
                'employee_name': log.employee_id.get_full_name(),
                'call_date': log.call_date.strftime('%Y-%m-%d'),
                'call_duration_minutes': log.call_duration_minutes,
                'call_count': log.call_count,
                'source': log.source,
                'created_at': log.created_at.isoformat()
            })
        
        return JsonResponse({
            'success': True,
            'data': data,
            'count': len(data)
        })
        
    except ValueError as e:
        return JsonResponse({
            'error': f'Invalid parameter: {str(e)}'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': f'Internal server error: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_calculate_attendance(request):
    """
    API endpoint to trigger attendance calculation
    
    Expected JSON payload:
    {
        "date": "2024-01-15"  // Optional, defaults to today
    }
    """
    try:
        data = json.loads(request.body) if request.body else {}
        
        # Parse target date
        target_date = date.today()
        if 'date' in data:
            target_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        
        # Calculate attendance
        result = CallAttendanceService.calculate_daily_attendance(target_date)
        
        return JsonResponse({
            'success': True,
            'message': 'Attendance calculation completed',
            'data': {
                'date': target_date.strftime('%Y-%m-%d'),
                'processed': result['processed'],
                'skipped': result['skipped'],
                'reason': result['reason']
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON payload'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': f'Internal server error: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
def api_get_attendance_summary(request):
    """
    API endpoint to get attendance summary
    
    Query parameters:
    - employee_id: Employee ID (required)
    - start_date: Start date (YYYY-MM-DD)
    - end_date: End date (YYYY-MM-DD)
    """
    try:
        employee_id = request.GET.get('employee_id')
        if not employee_id:
            return JsonResponse({
                'error': 'employee_id parameter is required'
            }, status=400)
        
        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return JsonResponse({
                'error': f'Employee with ID {employee_id} not found'
            }, status=404)
        
        # Parse date range
        start_date = None
        end_date = None
        
        if request.GET.get('start_date'):
            start_date = datetime.strptime(request.GET['start_date'], '%Y-%m-%d').date()
        
        if request.GET.get('end_date'):
            end_date = datetime.strptime(request.GET['end_date'], '%Y-%m-%d').date()
        
        # Get summary
        summary = CallAttendanceService.get_employee_attendance_summary(
            employee, start_date, end_date
        )
        
        return JsonResponse({
            'success': True,
            'data': {
                'employee_id': employee.id,
                'employee_name': employee.get_full_name(),
                'summary': summary,
                'period': {
                    'start_date': start_date.strftime('%Y-%m-%d') if start_date else None,
                    'end_date': end_date.strftime('%Y-%m-%d') if end_date else None
                }
            }
        })
        
    except ValueError as e:
        return JsonResponse({
            'error': f'Invalid parameter: {str(e)}'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': f'Internal server error: {str(e)}'
        }, status=500)


# API Documentation endpoint
@require_http_methods(["GET"])
def api_documentation(request):
    """
    API documentation endpoint
    """
    documentation = {
        'title': 'Call Attendance API',
        'version': '1.0',
        'description': 'Platform-agnostic API for call-based attendance management',
        'endpoints': {
            'POST /api/call-logs/create/': {
                'description': 'Create a single call log entry',
                'payload': {
                    'employee_id': 'integer (required)',
                    'call_date': 'string YYYY-MM-DD (required)',
                    'call_duration_minutes': 'integer (required)',
                    'call_count': 'integer (optional)',
                    'source': 'string (optional)'
                }
            },
            'POST /api/call-logs/bulk-create/': {
                'description': 'Bulk create call log entries',
                'payload': {
                    'call_logs': 'array of call log objects (required)',
                    'source': 'string (optional)'
                }
            },
            'GET /api/call-logs/': {
                'description': 'Retrieve call logs',
                'parameters': {
                    'employee_id': 'integer (optional)',
                    'date_from': 'string YYYY-MM-DD (optional)',
                    'date_to': 'string YYYY-MM-DD (optional)',
                    'limit': 'integer (optional, default: 100)'
                }
            },
            'POST /api/attendance/calculate/': {
                'description': 'Trigger attendance calculation',
                'payload': {
                    'date': 'string YYYY-MM-DD (optional, default: today)'
                }
            },
            'GET /api/attendance/summary/': {
                'description': 'Get attendance summary for employee',
                'parameters': {
                    'employee_id': 'integer (required)',
                    'start_date': 'string YYYY-MM-DD (optional)',
                    'end_date': 'string YYYY-MM-DD (optional)'
                }
            }
        },
        'authentication': 'API endpoints are currently open. Implement authentication as needed.',
        'rate_limiting': 'Not implemented. Consider adding rate limiting for production use.'
    }
    
    return JsonResponse(documentation, json_dumps_params={'indent': 2})