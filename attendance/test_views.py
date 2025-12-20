"""
Test view to create sample call attendance data
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from datetime import date, timedelta
import random

from employee.models import Employee
from attendance.call_attendance_models import CallAttendance


@login_required
def create_sample_data(request):
    """Create sample call attendance data for testing"""
    if request.method == 'POST':
        # Get active employees
        employees = Employee.objects.filter(is_active=True)[:5]
        
        if not employees.exists():
            messages.error(request, _('No active employees found. Please create some employees first.'))
            return redirect('attendance-view')

        created_count = 0
        
        # Create data for the last 7 days
        for i in range(7):
            attendance_date = date.today() - timedelta(days=i)
            
            for employee in employees:
                # Random call data
                call_duration = random.randint(60, 480)  # 1-8 hours in minutes
                call_count = random.randint(3, 30)
                
                # Determine status based on call duration
                if call_duration >= 240:  # 4+ hours
                    status = 'PRESENT'
                elif call_duration >= 120:  # 2-4 hours
                    status = 'HALF_DAY'
                else:
                    status = 'ABSENT'
                
                # Create attendance record if it doesn't exist
                attendance, created = CallAttendance.objects.get_or_create(
                    employee_id=employee,
                    attendance_date=attendance_date,
                    defaults={
                        'call_duration_minutes': call_duration,
                        'call_count': call_count,
                        'attendance_status': status,
                        'source': 'AUTO'
                    }
                )
                
                if created:
                    created_count += 1

        total_records = CallAttendance.objects.count()
        messages.success(request, 
            f'Created {created_count} new call attendance records. Total records: {total_records}')
        
        return redirect('attendance-view')
    
    # Show confirmation page
    context = {
        'total_employees': Employee.objects.filter(is_active=True).count(),
        'existing_records': CallAttendance.objects.count(),
    }
    
    return render(request, 'call_attendance/create_sample_data.html', context)