"""
Django management command for calculating call-based attendance.

Usage:
    python manage.py calculate_call_attendance
    python manage.py calculate_call_attendance --date 2024-01-15
    python manage.py calculate_call_attendance --days-back 7
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import date, datetime, timedelta
import logging

from attendance.call_attendance_services import CallAttendanceService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Calculate call-based attendance for employees'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Specific date to calculate attendance (YYYY-MM-DD format)'
        )
        parser.add_argument(
            '--days-back',
            type=int,
            help='Calculate attendance for the last N days'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force calculation even for non-working days'
        )

    def handle(self, *args, **options):
        try:
            target_dates = self.get_target_dates(options)
            
            total_processed = 0
            total_skipped = 0
            
            for target_date in target_dates:
                self.stdout.write(f"Processing attendance for {target_date}...")
                
                # Check if it's a working day (unless forced)
                if not options['force'] and not CallAttendanceService.is_working_day(target_date):
                    self.stdout.write(
                        self.style.WARNING(f"Skipping {target_date} - not a working day")
                    )
                    continue
                
                try:
                    result = CallAttendanceService.calculate_daily_attendance(target_date)
                    
                    total_processed += result['processed']
                    total_skipped += result['skipped']
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✓ {target_date}: Processed {result['processed']}, "
                            f"Skipped {result['skipped']}"
                        )
                    )
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"✗ {target_date}: Error - {str(e)}")
                    )
                    logger.error(f"Error calculating attendance for {target_date}: {str(e)}")
            
            # Summary
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nSummary: Total processed {total_processed}, "
                    f"Total skipped {total_skipped}"
                )
            )
            
        except Exception as e:
            raise CommandError(f"Command failed: {str(e)}")

    def get_target_dates(self, options):
        """Get list of target dates based on command options"""
        if options['date']:
            try:
                target_date = datetime.strptime(options['date'], '%Y-%m-%d').date()
                return [target_date]
            except ValueError:
                raise CommandError("Invalid date format. Use YYYY-MM-DD")
        
        elif options['days_back']:
            days_back = options['days_back']
            if days_back < 1:
                raise CommandError("days-back must be a positive integer")
            
            end_date = date.today()
            start_date = end_date - timedelta(days=days_back - 1)
            
            dates = []
            current_date = start_date
            while current_date <= end_date:
                dates.append(current_date)
                current_date += timedelta(days=1)
            
            return dates
        
        else:
            # Default: today
            return [date.today()]