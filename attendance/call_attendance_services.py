"""
Call-based Auto Attendance Services

This module contains business logic for calculating and managing
call-based attendance without external platform dependencies.
"""

from datetime import date, datetime
from typing import Dict, List, Optional, Tuple
from django.db import transaction
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError, PermissionDenied
from django.utils.translation import gettext_lazy as _

from employee.models import Employee
from base.methods import is_holiday, is_company_leave
from .call_attendance_models import (
    CallLog, CallAttendanceConfig, CallAttendance, CallAttendanceAudit
)


class CallAttendanceService:
    """
    Service class for call-based attendance operations
    """
    
    @staticmethod
    def get_active_config() -> Optional[CallAttendanceConfig]:
        """Get the active attendance configuration"""
        return CallAttendanceConfig.objects.filter(is_active=True).first()
    
    @staticmethod
    def calculate_attendance_status(call_minutes: int, config: CallAttendanceConfig) -> str:
        """
        Calculate attendance status based on call duration and configuration
        
        Args:
            call_minutes: Total call duration in minutes
            config: Active attendance configuration
            
        Returns:
            Attendance status: 'PRESENT', 'HALF_DAY', or 'ABSENT'
        """
        if call_minutes >= config.full_day_minutes:
            return 'PRESENT'
        elif call_minutes >= config.half_day_minutes:
            return 'HALF_DAY'
        else:
            return 'ABSENT'
    
    @staticmethod
    def is_working_day(target_date: date) -> bool:
        """
        Check if the given date is a working day
        
        Args:
            target_date: Date to check
            
        Returns:
            True if working day, False if holiday/weekend
        """
        # Skip Sundays
        if target_date.weekday() == 6:  # Sunday = 6
            return False
            
        # Skip holidays and company leaves
        if is_holiday(target_date) or is_company_leave(target_date):
            return False
            
        return True
    
    @classmethod
    def calculate_daily_attendance(cls, target_date: date = None) -> Dict[str, int]:
        """
        Calculate attendance for all employees for a specific date
        
        Args:
            target_date: Date to calculate attendance for (default: today)
            
        Returns:
            Dictionary with calculation statistics
        """
        if target_date is None:
            target_date = date.today()
            
        # Skip non-working days
        if not cls.is_working_day(target_date):
            return {
                'processed': 0,
                'skipped': 0,
                'reason': 'Non-working day'
            }
        
        config = cls.get_active_config()
        if not config:
            raise ValidationError(_("No active call attendance configuration found"))
        
        processed = 0
        skipped = 0
        
        # Get all call logs for the target date
        call_logs = CallLog.objects.filter(call_date=target_date)
        
        with transaction.atomic():
            for call_log in call_logs:
                # Skip if manual attendance already exists
                existing_attendance = CallAttendance.objects.filter(
                    employee_id=call_log.employee_id,
                    attendance_date=target_date,
                    source='MANUAL'
                ).first()
                
                if existing_attendance:
                    skipped += 1
                    continue
                
                # Calculate attendance status
                status = cls.calculate_attendance_status(
                    call_log.call_duration_minutes, 
                    config
                )
                
                # Create or update attendance record
                attendance, created = CallAttendance.objects.update_or_create(
                    employee_id=call_log.employee_id,
                    attendance_date=target_date,
                    defaults={
                        'call_duration_minutes': call_log.call_duration_minutes,
                        'call_count': call_log.call_count,
                        'attendance_status': status,
                        'source': 'AUTO',
                        'manual_reason': None,
                        'updated_by': None,
                    }
                )
                processed += 1
        
        return {
            'processed': processed,
            'skipped': skipped,
            'reason': 'Success'
        }
    
    @staticmethod
    def can_update_attendance(user: User) -> bool:
        """
        Check if user has permission to manually update attendance
        
        Args:
            user: User to check permissions for
            
        Returns:
            True if user can update attendance
        """
        if user.is_superuser:
            return True
            
        # Check if user is Team Leader or Manager
        try:
            employee = user.employee_get
            work_info = employee.employee_work_info
            
            # Check job position for TL/Manager roles
            if work_info.job_position_id:
                position_name = work_info.job_position_id.job_position.lower()
                if any(role in position_name for role in ['team leader', 'manager', 'tl']):
                    return True
            
            # Check if user has specific permission
            return user.has_perm('attendance.manual_update_call_attendance')
            
        except (AttributeError, Employee.DoesNotExist):
            return False
    
    @classmethod
    def manual_update_attendance(
        cls,
        employee_id: int,
        attendance_date: date,
        call_duration: int,
        call_count: int,
        updated_by_user: User
    ) -> CallAttendance:
        """
        Manually update call attendance with audit trail
        
        Args:
            employee_id: Employee ID
            attendance_date: Date of attendance
            call_duration: New call duration in minutes
            call_count: New call count
            updated_by_user: User making the update
            
        Returns:
            Updated CallAttendance instance
            
        Raises:
            PermissionDenied: If user lacks permission
            ValidationError: If validation fails
        """
        # Check permissions
        if not cls.can_update_attendance(updated_by_user):
            raise PermissionDenied(_("You don't have permission to update attendance"))
        
        # Get updater employee
        try:
            updated_by = updated_by_user.employee_get
        except Employee.DoesNotExist:
            raise ValidationError(_("User must be associated with an employee"))
        
        # Get employee
        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            raise ValidationError(_("Employee not found"))
        
        # Get active configuration
        config = cls.get_active_config()
        if not config:
            raise ValidationError(_("No active call attendance configuration found"))
        
        # Calculate new status
        new_status = cls.calculate_attendance_status(call_duration, config)
        
        with transaction.atomic():
            # Get existing attendance or create new
            attendance, created = CallAttendance.objects.get_or_create(
                employee_id=employee,
                attendance_date=attendance_date,
                defaults={
                    'call_duration_minutes': 0,
                    'call_count': 0,
                    'attendance_status': 'ABSENT',
                    'source': 'AUTO'
                }
            )
            
            # Store old values for audit
            old_duration = attendance.call_duration_minutes
            old_count = attendance.call_count
            old_status = attendance.attendance_status
            
            # Update attendance
            attendance.call_duration_minutes = call_duration
            attendance.call_count = call_count
            attendance.attendance_status = new_status
            attendance.source = 'MANUAL'
            attendance.manual_reason = 'Manual update'
            attendance.updated_by = updated_by
            attendance.save()
            
            # Create audit record
            CallAttendanceAudit.objects.create(
                call_attendance=attendance,
                employee_id=employee,
                attendance_date=attendance_date,
                old_call_duration=old_duration,
                old_call_count=old_count,
                old_status=old_status,
                new_call_duration=call_duration,
                new_call_count=call_count,
                new_status=new_status,
                reason='Manual update',
                updated_by=updated_by
            )
        
        return attendance
    
    @staticmethod
    def get_employee_attendance_summary(
        employee: Employee,
        start_date: date = None,
        end_date: date = None
    ) -> Dict:
        """
        Get attendance summary for an employee
        
        Args:
            employee: Employee instance
            start_date: Start date for summary (default: current month start)
            end_date: End date for summary (default: today)
            
        Returns:
            Dictionary with attendance summary
        """
        if not start_date:
            today = date.today()
            start_date = date(today.year, today.month, 1)
        if not end_date:
            end_date = date.today()
        
        attendances = CallAttendance.objects.filter(
            employee_id=employee,
            attendance_date__range=[start_date, end_date]
        )
        
        summary = {
            'total_days': attendances.count(),
            'present_days': attendances.filter(attendance_status='PRESENT').count(),
            'half_days': attendances.filter(attendance_status='HALF_DAY').count(),
            'absent_days': attendances.filter(attendance_status='ABSENT').count(),
            'total_call_minutes': sum(a.call_duration_minutes for a in attendances),
            'total_calls': sum(a.call_count for a in attendances),
            'manual_updates': attendances.filter(source='MANUAL').count(),
        }
        
        return summary
    
    @staticmethod
    def get_audit_trail(
        employee: Employee = None,
        start_date: date = None,
        end_date: date = None
    ) -> List[CallAttendanceAudit]:
        """
        Get audit trail for attendance updates
        
        Args:
            employee: Filter by employee (optional)
            start_date: Start date filter (optional)
            end_date: End date filter (optional)
            
        Returns:
            List of audit records
        """
        queryset = CallAttendanceAudit.objects.all()
        
        if employee:
            queryset = queryset.filter(employee_id=employee)
        if start_date:
            queryset = queryset.filter(attendance_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(attendance_date__lte=end_date)
            
        return queryset.order_by('-timestamp')


class CallLogService:
    """
    Service class for managing call logs
    """
    
    @staticmethod
    def create_call_log(
        employee: Employee,
        call_date: date,
        call_duration_minutes: int,
        call_count: int = 0,
        source: str = "MANUAL"
    ) -> CallLog:
        """
        Create or update call log entry
        
        Args:
            employee: Employee instance
            call_date: Date of calls
            call_duration_minutes: Total call duration in minutes
            call_count: Number of calls made
            source: Data source identifier
            
        Returns:
            CallLog instance
        """
        call_log, created = CallLog.objects.update_or_create(
            employee_id=employee,
            call_date=call_date,
            defaults={
                'call_duration_minutes': call_duration_minutes,
                'call_count': call_count,
                'source': source,
            }
        )
        return call_log
    
    @staticmethod
    def bulk_create_call_logs(call_data: List[Dict]) -> Tuple[int, int]:
        """
        Bulk create call logs from data
        
        Args:
            call_data: List of dictionaries with call log data
            
        Returns:
            Tuple of (created_count, updated_count)
        """
        created_count = 0
        updated_count = 0
        
        with transaction.atomic():
            for data in call_data:
                try:
                    employee = Employee.objects.get(id=data['employee_id'])
                    call_log, created = CallLog.objects.update_or_create(
                        employee_id=employee,
                        call_date=data['call_date'],
                        defaults={
                            'call_duration_minutes': data['call_duration_minutes'],
                            'call_count': data.get('call_count', 0),
                            'source': data.get('source', 'API'),
                        }
                    )
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                except Employee.DoesNotExist:
                    continue  # Skip invalid employee IDs
        
        return created_count, updated_count