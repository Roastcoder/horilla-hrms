"""
Sales Organization Validation Framework

Comprehensive validation system for attendance, incentives, targets, and audit trail.
"""

from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from datetime import date, datetime
from decimal import Decimal
import re
from base.templatetags.basefilters import is_reportingmanager
from employee.models import Employee
from base.models import Company


class SalesValidationError(ValidationError):
    """Custom validation error for sales operations"""
    pass


class RoleValidator:
    """Role-based permission validation"""
    
    @staticmethod
    def can_update_attendance(user):
        """Check if user can update attendance"""
        return (
            user.is_superuser or 
            user.has_perm('attendance.change_callattendance') or
            is_reportingmanager(user)
        )
    
    @staticmethod
    def can_approve_incentives(user):
        """Check if user can approve incentives"""
        return user.is_superuser or user.has_perm('sales_incentive.change_incentiveslab')
    
    @staticmethod
    def get_accessible_employees(user):
        """Get employees accessible to user based on role"""
        if user.is_superuser:
            return Employee.objects.filter(is_active=True)
        elif is_reportingmanager(user):
            return Employee.objects.filter(
                employee_work_info__reporting_manager_id=user.employee_get,
                is_active=True
            )
        else:
            return Employee.objects.filter(id=user.employee_get.id, is_active=True)


class AttendanceValidator:
    """Attendance validation rules"""
    
    ATTENDANCE_RULES = {
        'PRESENT': {'min_minutes': 171, 'max_minutes': None},
        'HALF_DAY': {'min_minutes': 121, 'max_minutes': 170},
        'ABSENT': {'min_minutes': 0, 'max_minutes': 120}
    }
    
    @classmethod
    def validate_manual_update(cls, data, user):
        """Validate manual attendance update"""
        errors = {}
        
        # Employee validation
        if not data.get('employee_id'):
            errors['employee_id'] = _("Employee is required")
        else:
            accessible_employees = RoleValidator.get_accessible_employees(user)
            if not accessible_employees.filter(id=data['employee_id']).exists():
                errors['employee_id'] = _("You don't have permission to update this employee")
        
        # Date validation
        if not data.get('attendance_date'):
            errors['attendance_date'] = _("Attendance date is required")
        else:
            attendance_date = data['attendance_date']
            if isinstance(attendance_date, str):
                try:
                    attendance_date = datetime.strptime(attendance_date, '%Y-%m-%d').date()
                except ValueError:
                    errors['attendance_date'] = _("Invalid date format")
            
            if attendance_date and attendance_date.weekday() == 6:  # Sunday
                errors['attendance_date'] = _("No attendance allowed on Sundays")
        
        # Call duration validation
        call_duration = data.get('call_duration_minutes', 0)
        if not isinstance(call_duration, (int, float)) or call_duration < 0:
            errors['call_duration_minutes'] = _("Call duration must be a positive number")
        
        # Call count validation
        call_count = data.get('call_count', 0)
        if not isinstance(call_count, int) or call_count < 0:
            errors['call_count'] = _("Call count must be a positive integer")
        
        # Reason validation for manual updates
        reason = data.get('reason', '')
        if not reason or len(reason.strip()) < 10:
            errors['reason'] = _("Reason is required and must be at least 10 characters")
        
        # Loan amount validation
        loan_amount = data.get('loan_amount', 0)
        if loan_amount and (not isinstance(loan_amount, (int, float, Decimal)) or loan_amount < 0):
            errors['loan_amount'] = _("Loan amount must be a positive number")
        
        if errors:
            raise SalesValidationError(errors)
        
        return True
    
    @classmethod
    def calculate_attendance_status(cls, call_duration_minutes):
        """Calculate attendance status based on call duration"""
        if call_duration_minutes >= 171:
            return 'PRESENT'
        elif call_duration_minutes >= 121:
            return 'HALF_DAY'
        else:
            return 'ABSENT'
    
    @classmethod
    def validate_attendance_logic(cls, call_duration_minutes, expected_status=None):
        """Validate attendance logic consistency"""
        calculated_status = cls.calculate_attendance_status(call_duration_minutes)
        
        if expected_status and expected_status != calculated_status:
            raise SalesValidationError({
                'status': _(f"Status should be {calculated_status} for {call_duration_minutes} minutes")
            })
        
        return calculated_status


class IncentiveValidator:
    """Incentive calculation validation"""
    
    INCENTIVE_SLABS = [
        {'min_lac': 1, 'max_lac': 5, 'rate': 300},
        {'min_lac': 6, 'max_lac': 10, 'rate': 400},
        {'min_lac': 11, 'max_lac': 15, 'rate': 500},
        {'min_lac': 16, 'max_lac': 20, 'rate': 600},
        {'min_lac': 21, 'max_lac': 25, 'rate': 700},
        {'min_lac': 26, 'max_lac': 30, 'rate': 750},
        {'min_lac': 31, 'max_lac': 35, 'rate': 800},
        {'min_lac': 36, 'max_lac': 40, 'rate': 850},
        {'min_lac': 41, 'max_lac': 45, 'rate': 900},
        {'min_lac': 46, 'max_lac': 50, 'rate': 950},
        {'min_lac': 51, 'max_lac': None, 'rate': 1000},
    ]
    
    @classmethod
    def calculate_incentive(cls, loan_amount_lac):
        """Calculate incentive based on loan amount in lacs"""
        if not isinstance(loan_amount_lac, (int, float, Decimal)) or loan_amount_lac <= 0:
            raise SalesValidationError({'loan_amount': _("Loan amount must be positive")})
        
        total_incentive = 0
        remaining_amount = loan_amount_lac
        
        for slab in cls.INCENTIVE_SLABS:
            if remaining_amount <= 0:
                break
            
            slab_min = slab['min_lac']
            slab_max = slab['max_lac']
            rate = slab['rate']
            
            if slab_max is None:  # 51+ lac slab
                slab_amount = remaining_amount
            else:
                slab_amount = min(remaining_amount, slab_max - slab_min + 1)
            
            if loan_amount_lac >= slab_min:
                if slab_max is None or loan_amount_lac >= slab_min:
                    applicable_amount = min(slab_amount, remaining_amount)
                    total_incentive += applicable_amount * rate
                    remaining_amount -= applicable_amount
        
        return total_incentive
    
    @classmethod
    def validate_incentive_data(cls, data):
        """Validate incentive calculation data"""
        errors = {}
        
        loan_amount = data.get('loan_amount', 0)
        if not isinstance(loan_amount, (int, float, Decimal)) or loan_amount < 0:
            errors['loan_amount'] = _("Loan amount must be a positive number")
        
        loan_type = data.get('loan_type', '')
        if not loan_type:
            errors['loan_type'] = _("Loan type is required")
        
        if errors:
            raise SalesValidationError(errors)
        
        return True


class LoanPointValidator:
    """Loan-wise point system validation"""
    
    LOAN_POINTS = {
        'HOME_LOAN': 0.2,
        'LAP': 0.3,
        'CV_LOAN': 0.2,
        'PERSONAL_LOAN': 1.0,
        'BUSINESS_LOAN': 1.0,
        'USED_CAR_LOAN': 1.0,
        'NEW_CAR_LOAN': 0.2,
    }
    
    @classmethod
    def calculate_points(cls, loan_type, loan_amount_lac):
        """Calculate points based on loan type and amount"""
        if loan_type not in cls.LOAN_POINTS:
            raise SalesValidationError({'loan_type': _("Invalid loan type")})
        
        if not isinstance(loan_amount_lac, (int, float, Decimal)) or loan_amount_lac <= 0:
            raise SalesValidationError({'loan_amount': _("Loan amount must be positive")})
        
        point_rate = cls.LOAN_POINTS[loan_type]
        return loan_amount_lac * point_rate
    
    @classmethod
    def validate_loan_data(cls, data):
        """Validate loan data"""
        errors = {}
        
        loan_type = data.get('loan_type', '')
        if loan_type not in cls.LOAN_POINTS:
            errors['loan_type'] = _("Invalid loan type. Valid types: {}".format(
                ', '.join(cls.LOAN_POINTS.keys())
            ))
        
        loan_amount = data.get('loan_amount', 0)
        if not isinstance(loan_amount, (int, float, Decimal)) or loan_amount <= 0:
            errors['loan_amount'] = _("Loan amount must be positive")
        
        if errors:
            raise SalesValidationError(errors)
        
        return True


class TargetSalaryValidator:
    """Target and salary validation"""
    
    @classmethod
    def validate_target_salary_mapping(cls, data):
        """Validate target and salary mapping"""
        errors = {}
        
        salary = data.get('salary', 0)
        if not isinstance(salary, (int, float, Decimal)) or salary <= 0:
            errors['salary'] = _("Salary must be positive")
        
        auto_target = data.get('auto_target', 0)
        manual_target = data.get('manual_target', 0)
        
        if salary > 0:
            # Target = Salary in Lac ratio
            calculated_target = salary / 100000  # Convert to lacs
            
            if auto_target and abs(auto_target - calculated_target) > 0.01:
                errors['auto_target'] = _("Auto target should match salary in lac ratio")
        
        # Final target = MAX(auto_target, manual_target)
        final_target = max(auto_target or 0, manual_target or 0)
        if final_target <= 0:
            errors['target'] = _("Final target must be positive")
        
        if errors:
            raise SalesValidationError(errors)
        
        return final_target


class WaiverPresenceValidator:
    """Waiver and presence rules validation"""
    
    MAX_WAIVER_PERCENTAGE = 30
    
    @classmethod
    def validate_waiver_rules(cls, data):
        """Validate waiver and presence rules"""
        errors = {}
        
        total_days = data.get('total_days', 0)
        present_days = data.get('present_days', 0)
        waiver_days = data.get('waiver_days', 0)
        
        if total_days <= 0:
            errors['total_days'] = _("Total days must be positive")
        
        if present_days < 0 or present_days > total_days:
            errors['present_days'] = _("Present days must be between 0 and total days")
        
        if waiver_days < 0:
            errors['waiver_days'] = _("Waiver days cannot be negative")
        
        # Calculate waiver percentage
        if total_days > 0:
            waiver_percentage = (waiver_days / total_days) * 100
            if waiver_percentage > cls.MAX_WAIVER_PERCENTAGE:
                errors['waiver_days'] = _(f"Waiver cannot exceed {cls.MAX_WAIVER_PERCENTAGE}%")
        
        # Physical presence mandatory
        physical_presence = data.get('physical_presence', False)
        if not physical_presence:
            errors['physical_presence'] = _("Physical presence is mandatory")
        
        if errors:
            raise SalesValidationError(errors)
        
        return True


class AuditValidator:
    """Audit and security validation"""
    
    @classmethod
    def create_audit_log(cls, model_instance, user, action, old_values=None, new_values=None, reason=None):
        """Create audit log entry"""
        from attendance.call_attendance_models import CallAttendanceAudit
        
        audit_data = {
            'employee_id': getattr(model_instance, 'employee_id', None),
            'updated_by': user,
            'action': action,
            'timestamp': datetime.now(),
            'old_values': old_values or {},
            'new_values': new_values or {},
            'reason': reason or '',
            'ip_address': cls.get_client_ip(getattr(cls, '_request', None))
        }
        
        return CallAttendanceAudit.objects.create(**audit_data)
    
    @staticmethod
    def get_client_ip(request):
        """Get client IP address"""
        if not request:
            return None
        
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    @classmethod
    def validate_csrf_and_duplicates(cls, request, unique_key=None):
        """Validate CSRF and prevent duplicate submissions"""
        # CSRF validation is handled by Django middleware
        
        # Duplicate submission check
        if unique_key:
            cache_key = f"submission_{request.user.id}_{unique_key}"
            from django.core.cache import cache
            
            if cache.get(cache_key):
                raise SalesValidationError({'duplicate': _("Duplicate submission detected")})
            
            # Set cache for 60 seconds to prevent duplicates
            cache.set(cache_key, True, 60)
        
        return True


class ComprehensiveValidator:
    """Main validation orchestrator"""
    
    def __init__(self, request=None):
        self.request = request
        if request:
            AuditValidator._request = request
    
    def validate_attendance_update(self, data, user):
        """Comprehensive attendance update validation"""
        # Role validation
        if not RoleValidator.can_update_attendance(user):
            raise SalesValidationError({'permission': _("Insufficient permissions")})
        
        # Data validation
        AttendanceValidator.validate_manual_update(data, user)
        
        # CSRF and duplicate check
        if self.request:
            unique_key = f"attendance_{data.get('employee_id')}_{data.get('attendance_date')}"
            AuditValidator.validate_csrf_and_duplicates(self.request, unique_key)
        
        return True
    
    def validate_incentive_calculation(self, data, user):
        """Comprehensive incentive validation"""
        # Role validation
        if not RoleValidator.can_approve_incentives(user):
            raise SalesValidationError({'permission': _("Insufficient permissions")})
        
        # Data validation
        IncentiveValidator.validate_incentive_data(data)
        LoanPointValidator.validate_loan_data(data)
        
        return True
    
    def validate_complete_workflow(self, attendance_data, incentive_data, user):
        """Validate complete sales workflow"""
        errors = {}
        
        try:
            self.validate_attendance_update(attendance_data, user)
        except SalesValidationError as e:
            errors.update({'attendance': e.message_dict})
        
        try:
            self.validate_incentive_calculation(incentive_data, user)
        except SalesValidationError as e:
            errors.update({'incentive': e.message_dict})
        
        if errors:
            raise SalesValidationError(errors)
        
        return True