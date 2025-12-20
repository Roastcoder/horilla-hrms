"""
Sales Incentive Integration Service

Service to integrate sales incentive system with existing Horilla modules.
"""

from django.db.models import Sum, Q
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal

from attendance.call_attendance_models import CallAttendance
from employee.models import Employee
from .sales_incentive_models import (
    IncentiveCalculation, SalesTarget, Lead, 
    CallAttendanceConfig, IncentiveSlab
)


class SalesIncentiveService:
    """Service class for sales incentive calculations and integrations"""
    
    @staticmethod
    def calculate_monthly_incentive(employee, month):
        """Calculate incentive for an employee for a specific month"""
        try:
            calculation, created = IncentiveCalculation.objects.get_or_create(
                employee=employee,
                month=month,
                defaults={'waiver_percentage': 30}
            )
            
            calculation.calculate_incentive()
            return calculation
        except Exception as e:
            print(f"Error calculating incentive for {employee}: {e}")
            return None
    
    @staticmethod
    def get_employee_performance_summary(employee, start_date, end_date):
        """Get comprehensive performance summary for an employee"""
        leads = Lead.objects.filter(
            employee=employee,
            created_date__range=[start_date, end_date]
        )
        
        disbursed_leads = leads.filter(status='DISBURSED')
        
        summary = {
            'total_leads': leads.count(),
            'disbursed_leads': disbursed_leads.count(),
            'conversion_rate': (disbursed_leads.count() / leads.count() * 100) if leads.count() > 0 else 0,
            'total_amount': disbursed_leads.aggregate(total=Sum('loan_amount'))['total'] or 0,
            'total_points': sum(lead.points_earned for lead in disbursed_leads),
            'avg_loan_size': disbursed_leads.aggregate(avg=Sum('loan_amount'))['avg'] or 0,
        }
        
        # Add call attendance data
        call_attendances = CallAttendance.objects.filter(
            employee_id=employee,
            attendance_date__range=[start_date, end_date]
        )
        
        summary.update({
            'total_call_days': call_attendances.count(),
            'present_days': call_attendances.filter(attendance_status='PRESENT').count(),
            'half_days': call_attendances.filter(attendance_status='HALF_DAY').count(),
            'absent_days': call_attendances.filter(attendance_status='ABSENT').count(),
            'attendance_rate': (call_attendances.exclude(attendance_status='ABSENT').count() / 
                             call_attendances.count() * 100) if call_attendances.count() > 0 else 0,
        })
        
        return summary
    
    @staticmethod
    def check_salary_eligibility(employee, month):
        """Check if employee is eligible for salary based on attendance and performance"""
        # Get call attendance for the month
        call_attendances = CallAttendance.objects.filter(
            employee_id=employee,
            attendance_date__year=month.year,
            attendance_date__month=month.month
        )
        
        if not call_attendances.exists():
            return False, "No attendance records found"
        
        # Calculate attendance percentage
        total_days = call_attendances.count()
        present_days = call_attendances.exclude(attendance_status='ABSENT').count()
        attendance_percentage = (present_days / total_days * 100) if total_days > 0 else 0
        
        # Check minimum attendance requirement (70% considering 30% waiver)
        if attendance_percentage < 70:
            return False, f"Attendance below threshold: {attendance_percentage:.1f}%"
        
        # Check if there are any disbursed leads (performance requirement)
        disbursed_leads = Lead.objects.filter(
            employee=employee,
            status='DISBURSED',
            disbursed_date__year=month.year,
            disbursed_date__month=month.month
        )
        
        if not disbursed_leads.exists():
            return False, "No disbursed loans in the month"
        
        return True, "Eligible for salary"
    
    @staticmethod
    def auto_create_targets_from_salary():
        """Auto-create targets based on employee salaries"""
        employees = Employee.objects.filter(is_active=True)
        current_month = date.today().replace(day=1)
        
        created_count = 0
        for employee in employees:
            if (employee.employee_work_info and 
                employee.employee_work_info.basic_salary):
                
                target_amount = employee.employee_work_info.basic_salary / 1000  # Convert to Lac
                
                target, created = SalesTarget.objects.get_or_create(
                    employee=employee,
                    month=current_month,
                    defaults={
                        'target_amount': target_amount,
                        'auto_target_amount': target_amount,
                        'final_target_amount': target_amount
                    }
                )
                
                if created:
                    created_count += 1
        
        return created_count
    
    @staticmethod
    def get_incentive_preview(loan_amount_lac):
        """Preview incentive calculation for a given loan amount"""
        slabs = IncentiveSlab.objects.filter(is_active=True).order_by('min_amount')
        
        incentive_breakdown = []
        total_incentive = 0
        remaining_amount = loan_amount_lac
        
        for slab in slabs:
            if remaining_amount <= 0:
                break
                
            if remaining_amount >= slab.min_amount:
                # Calculate amount in this slab
                slab_max = slab.max_amount or float('inf')
                slab_amount = min(
                    remaining_amount - slab.min_amount + 1,
                    slab_max - slab.min_amount + 1
                )
                
                if slab_amount > 0:
                    slab_incentive = slab_amount * slab.incentive_per_lac
                    total_incentive += slab_incentive
                    
                    incentive_breakdown.append({
                        'slab': f"{slab.min_amount}-{slab.max_amount or '∞'} Lac",
                        'amount': slab_amount,
                        'rate': slab.incentive_per_lac,
                        'incentive': slab_incentive
                    })
                    
                    remaining_amount -= slab_amount
        
        return {
            'total_incentive': total_incentive,
            'breakdown': incentive_breakdown,
            'final_incentive_after_waiver': total_incentive * 0.7  # 30% waiver
        }
    
    @staticmethod
    def bulk_calculate_incentives(month, employee_ids=None):
        """Bulk calculate incentives for multiple employees"""
        if employee_ids:
            employees = Employee.objects.filter(id__in=employee_ids, is_active=True)
        else:
            employees = Employee.objects.filter(is_active=True)
        
        results = {
            'success': 0,
            'errors': 0,
            'details': []
        }
        
        for employee in employees:
            try:
                calculation = SalesIncentiveService.calculate_monthly_incentive(employee, month)
                if calculation:
                    results['success'] += 1
                    results['details'].append({
                        'employee': str(employee),
                        'status': 'success',
                        'incentive': float(calculation.final_incentive)
                    })
                else:
                    results['errors'] += 1
                    results['details'].append({
                        'employee': str(employee),
                        'status': 'error',
                        'message': 'Calculation failed'
                    })
            except Exception as e:
                results['errors'] += 1
                results['details'].append({
                    'employee': str(employee),
                    'status': 'error',
                    'message': str(e)
                })
        
        return results


class CallAttendanceIntegration:
    """Integration with existing call attendance system"""
    
    @staticmethod
    def sync_call_attendance_config():
        """Sync call attendance configuration with sales config"""
        from attendance.call_attendance_models import CallAttendanceConfig as ExistingConfig
        
        sales_config = CallAttendanceConfig.objects.filter(is_active=True).first()
        if not sales_config:
            return False
        
        # Update existing call attendance config
        existing_config = ExistingConfig.objects.first()
        if existing_config:
            existing_config.full_day_minutes = sales_config.present_threshold
            existing_config.half_day_minutes = sales_config.half_day_threshold
            existing_config.absent_threshold_minutes = sales_config.absent_threshold
            existing_config.save()
            return True
        
        return False
    
    @staticmethod
    def get_attendance_summary_for_incentive(employee, month):
        """Get attendance summary specifically for incentive calculation"""
        call_attendances = CallAttendance.objects.filter(
            employee_id=employee,
            attendance_date__year=month.year,
            attendance_date__month=month.month
        )
        
        summary = {
            'total_days': call_attendances.count(),
            'present_days': call_attendances.filter(attendance_status='PRESENT').count(),
            'half_days': call_attendances.filter(attendance_status='HALF_DAY').count(),
            'absent_days': call_attendances.filter(attendance_status='ABSENT').count(),
            'manual_updates': call_attendances.filter(source='MANUAL').count(),
        }
        
        # Calculate attendance percentage
        working_days = summary['present_days'] + summary['half_days']
        summary['attendance_percentage'] = (
            (working_days / summary['total_days'] * 100) 
            if summary['total_days'] > 0 else 0
        )
        
        # Check eligibility (70% threshold considering 30% waiver)
        summary['salary_eligible'] = summary['attendance_percentage'] >= 70
        
        return summary