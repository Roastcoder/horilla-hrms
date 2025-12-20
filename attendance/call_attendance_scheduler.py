"""
Call Attendance Scheduler

Automated scheduling for call-based attendance calculation.
This can be integrated with Django-Q, Celery, or cron jobs.
"""

import logging
from datetime import date, datetime, timedelta
from django.conf import settings
from django.core.management import call_command
from .call_attendance_services import CallAttendanceService

logger = logging.getLogger(__name__)


def calculate_daily_attendance_job(target_date=None):
    """
    Job function to calculate daily attendance
    
    Args:
        target_date: Date to calculate attendance for (default: today)
    """
    if target_date is None:
        target_date = date.today()
    
    try:
        logger.info(f"Starting attendance calculation for {target_date}")
        
        # Check if it's a working day
        if not CallAttendanceService.is_working_day(target_date):
            logger.info(f"Skipping {target_date} - not a working day")
            return
        
        # Calculate attendance
        result = CallAttendanceService.calculate_daily_attendance(target_date)
        
        logger.info(
            f"Attendance calculation completed for {target_date}. "
            f"Processed: {result['processed']}, Skipped: {result['skipped']}"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error calculating attendance for {target_date}: {str(e)}")
        raise


def calculate_attendance_for_date_range(start_date, end_date):
    """
    Calculate attendance for a range of dates
    
    Args:
        start_date: Start date
        end_date: End date
    """
    current_date = start_date
    results = []
    
    while current_date <= end_date:
        try:
            result = calculate_daily_attendance_job(current_date)
            if result:
                results.append({
                    'date': current_date,
                    'result': result
                })
        except Exception as e:
            logger.error(f"Failed to calculate attendance for {current_date}: {str(e)}")
            results.append({
                'date': current_date,
                'error': str(e)
            })
        
        current_date += timedelta(days=1)
    
    return results


# Django-Q integration (if available)
try:
    from django_q.tasks import schedule
    from django_q.models import Schedule
    
    def setup_daily_attendance_schedule():
        """
        Setup daily attendance calculation schedule using Django-Q
        """
        # Remove existing schedule if any
        Schedule.objects.filter(
            func='attendance.call_attendance_scheduler.calculate_daily_attendance_job'
        ).delete()
        
        # Schedule daily calculation at 11:59 PM
        schedule(
            'attendance.call_attendance_scheduler.calculate_daily_attendance_job',
            schedule_type=Schedule.DAILY,
            next_run=datetime.now().replace(hour=23, minute=59, second=0, microsecond=0),
            name='Daily Call Attendance Calculation'
        )
        
        logger.info("Daily attendance calculation schedule created")

except ImportError:
    logger.info("Django-Q not available. Use cron jobs or other scheduling methods.")
    
    def setup_daily_attendance_schedule():
        """
        Fallback function when Django-Q is not available
        """
        logger.warning(
            "Django-Q not available. Please set up a cron job to run: "
            "python manage.py calculate_call_attendance"
        )


# Celery integration (if available)
try:
    from celery import shared_task
    
    @shared_task
    def celery_calculate_daily_attendance(target_date_str=None):
        """
        Celery task for calculating daily attendance
        
        Args:
            target_date_str: Date string in YYYY-MM-DD format
        """
        if target_date_str:
            target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        else:
            target_date = date.today()
        
        return calculate_daily_attendance_job(target_date)
    
    @shared_task
    def celery_calculate_attendance_range(start_date_str, end_date_str):
        """
        Celery task for calculating attendance for a date range
        
        Args:
            start_date_str: Start date string in YYYY-MM-DD format
            end_date_str: End date string in YYYY-MM-DD format
        """
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        return calculate_attendance_for_date_range(start_date, end_date)

except ImportError:
    logger.info("Celery not available. Use Django-Q or cron jobs for scheduling.")


# Cron job helper functions
def get_cron_command():
    """
    Get the cron command for daily attendance calculation
    
    Returns:
        String with cron command
    """
    return (
        "0 23 * * * cd /path/to/your/project && "
        "python manage.py calculate_call_attendance"
    )


def get_cron_setup_instructions():
    """
    Get instructions for setting up cron job
    
    Returns:
        String with setup instructions
    """
    return f"""
To set up automated attendance calculation using cron:

1. Open crontab:
   crontab -e

2. Add the following line to run daily at 11:00 PM:
   {get_cron_command()}

3. Save and exit

Alternative: Run manually for specific dates:
   python manage.py calculate_call_attendance --date 2024-01-15
   python manage.py calculate_call_attendance --days-back 7
"""


# Utility functions for monitoring
def get_attendance_calculation_status():
    """
    Get status of recent attendance calculations
    
    Returns:
        Dictionary with status information
    """
    from .call_attendance_models import CallAttendance
    
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    # Check if today's attendance has been calculated
    today_count = CallAttendance.objects.filter(attendance_date=today).count()
    yesterday_count = CallAttendance.objects.filter(attendance_date=yesterday).count()
    
    # Get last calculation time (approximate)
    last_record = CallAttendance.objects.filter(
        source='AUTO'
    ).order_by('-created_at').first()
    
    return {
        'today_records': today_count,
        'yesterday_records': yesterday_count,
        'last_auto_calculation': last_record.created_at if last_record else None,
        'status': 'up_to_date' if today_count > 0 else 'pending'
    }


def cleanup_old_audit_logs(days_to_keep=90):
    """
    Clean up old audit logs to prevent database bloat
    
    Args:
        days_to_keep: Number of days to keep audit logs
    """
    from .call_attendance_models import CallAttendanceAudit
    
    cutoff_date = date.today() - timedelta(days=days_to_keep)
    
    deleted_count = CallAttendanceAudit.objects.filter(
        attendance_date__lt=cutoff_date
    ).delete()[0]
    
    logger.info(f"Cleaned up {deleted_count} old audit log entries")
    return deleted_count