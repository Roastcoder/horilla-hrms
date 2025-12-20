"""
Management command to create sample call attendance data for testing
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
import random

from employee.models import Employee
from attendance.call_attendance_models import CallAttendance


class Command(BaseCommand):
    help = 'Create sample call attendance data for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to create data for (default: 7)'
        )
        parser.add_argument(
            '--employees',
            type=int,
            default=5,
            help='Number of employees to create data for (default: 5)'
        )

    def handle(self, *args, **options):
        days = options['days']
        num_employees = options['employees']

        # Get active employees
        employees = Employee.objects.filter(is_active=True)[:num_employees]
        
        if not employees.exists():
            self.stdout.write(self.style.ERROR('No active employees found. Please create some employees first.'))
            return

        self.stdout.write(f'Creating sample data for {employees.count()} employees over {days} days...')

        created_count = 0
        updated_count = 0

        for i in range(days):
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
                
                # Create or update attendance record
                attendance, created = CallAttendance.objects.update_or_create(
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
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Created: {employee} on {attendance_date}: {status} ({call_duration} min, {call_count} calls)'
                        )
                    )
                else:
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f'Updated: {employee} on {attendance_date}: {status} ({call_duration} min, {call_count} calls)'
                        )
                    )

        total_records = CallAttendance.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSummary: Created {created_count}, Updated {updated_count}. Total records: {total_records}'
            )
        )
