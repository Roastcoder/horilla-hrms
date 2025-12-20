"""
Sales Incentive Forms

Forms for managing sales incentives, targets, and configurations.
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal

from employee.models import Employee
from .sales_incentive_models import (
    IncentiveSlab, LoanType, SalesTarget, Lead, 
    IncentiveCalculation, CallAttendanceConfig
)


class IncentiveSlabForm(forms.ModelForm):
    """Form for managing incentive slabs"""
    
    class Meta:
        model = IncentiveSlab
        fields = ['min_amount', 'max_amount', 'incentive_per_lac', 'is_active']
        widgets = {
            'min_amount': forms.NumberInput(attrs={'class': 'oh-input', 'step': '0.01'}),
            'max_amount': forms.NumberInput(attrs={'class': 'oh-input', 'step': '0.01'}),
            'incentive_per_lac': forms.NumberInput(attrs={'class': 'oh-input', 'step': '0.01'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        min_amount = cleaned_data.get('min_amount')
        max_amount = cleaned_data.get('max_amount')
        
        if min_amount and max_amount and min_amount >= max_amount:
            raise forms.ValidationError(_("Maximum amount must be greater than minimum amount"))
        
        return cleaned_data


class LoanTypeForm(forms.ModelForm):
    """Form for managing loan types"""
    
    class Meta:
        model = LoanType
        fields = ['name', 'points_per_lac', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'oh-input'}),
            'points_per_lac': forms.NumberInput(attrs={'class': 'oh-input', 'step': '0.01'}),
        }


class SalesTargetForm(forms.ModelForm):
    """Form for setting sales targets"""
    
    class Meta:
        model = SalesTarget
        fields = ['employee', 'month', 'target_amount']
        widgets = {
            'employee': forms.Select(attrs={'class': 'oh-select'}),
            'month': forms.DateInput(attrs={'class': 'oh-input', 'type': 'month'}),
            'target_amount': forms.NumberInput(attrs={'class': 'oh-input', 'step': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = Employee.objects.filter(is_active=True)


class LeadForm(forms.ModelForm):
    """Form for managing leads"""
    
    class Meta:
        model = Lead
        fields = [
            'employee', 'loan_type', 'loan_amount', 'status',
            'ac_new_api', 'kyc_api', 'aip', 'disbursed_date'
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': 'oh-select'}),
            'loan_type': forms.Select(attrs={'class': 'oh-select'}),
            'loan_amount': forms.NumberInput(attrs={'class': 'oh-input', 'step': '0.01'}),
            'status': forms.Select(attrs={'class': 'oh-select'}),
            'disbursed_date': forms.DateTimeInput(attrs={'class': 'oh-input', 'type': 'datetime-local'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = Employee.objects.filter(is_active=True)
        self.fields['loan_type'].queryset = LoanType.objects.filter(is_active=True)
        self.fields['disbursed_date'].required = False


class IncentiveCalculationForm(forms.ModelForm):
    """Form for incentive calculations"""
    
    class Meta:
        model = IncentiveCalculation
        fields = ['employee', 'month', 'waiver_percentage']
        widgets = {
            'employee': forms.Select(attrs={'class': 'oh-select'}),
            'month': forms.DateInput(attrs={'class': 'oh-input', 'type': 'month'}),
            'waiver_percentage': forms.NumberInput(attrs={'class': 'oh-input', 'step': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = Employee.objects.filter(is_active=True)


class CallAttendanceConfigForm(forms.ModelForm):
    """Form for call attendance configuration"""
    
    class Meta:
        model = CallAttendanceConfig
        fields = [
            'daily_required_minutes', 'present_threshold', 
            'half_day_threshold', 'absent_threshold', 'is_active'
        ]
        widgets = {
            'daily_required_minutes': forms.NumberInput(attrs={'class': 'oh-input'}),
            'present_threshold': forms.NumberInput(attrs={'class': 'oh-input'}),
            'half_day_threshold': forms.NumberInput(attrs={'class': 'oh-input'}),
            'absent_threshold': forms.NumberInput(attrs={'class': 'oh-input'}),
        }


class BulkIncentiveCalculationForm(forms.Form):
    """Form for bulk incentive calculation"""
    
    month = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'oh-input', 'type': 'month'}),
        label=_("Month")
    )
    employees = forms.ModelMultipleChoiceField(
        queryset=Employee.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label=_("Employees (leave blank for all)")
    )
    recalculate = forms.BooleanField(
        required=False,
        label=_("Recalculate existing records")
    )


class ReportFilterForm(forms.Form):
    """Form for filtering reports"""
    
    REPORT_TYPES = [
        ('incentive', _('Incentive Report')),
        ('attendance', _('Attendance Report')),
        ('target_achievement', _('Target vs Achievement')),
        ('points_summary', _('Points Summary')),
    ]
    
    report_type = forms.ChoiceField(
        choices=REPORT_TYPES,
        widget=forms.Select(attrs={'class': 'oh-select'}),
        label=_("Report Type")
    )
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'oh-input', 'type': 'date'}),
        label=_("Start Date")
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'oh-input', 'type': 'date'}),
        label=_("End Date")
    )
    employees = forms.ModelMultipleChoiceField(
        queryset=Employee.objects.filter(is_active=True),
        widget=forms.SelectMultiple(attrs={'class': 'oh-select'}),
        required=False,
        label=_("Employees (leave blank for all)")
    )