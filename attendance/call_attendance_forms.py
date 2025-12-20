"""
Call-based Auto Attendance Forms

Forms for managing call logs, attendance configuration, and manual updates.
"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from datetime import date

from employee.models import Employee
from .call_attendance_models import (
    CallLog, CallAttendanceConfig, CallAttendance
)


class CallLogForm(forms.ModelForm):
    """Form for creating/updating call logs"""
    
    class Meta:
        model = CallLog
        fields = [
            'employee_id', 'call_date', 'call_duration_minutes', 
            'call_count', 'source'
        ]
        widgets = {
            'call_date': forms.DateInput(attrs={'type': 'date'}),
            'call_duration_minutes': forms.NumberInput(attrs={'min': 0}),
            'call_count': forms.NumberInput(attrs={'min': 0}),
        }
    
    def clean_call_date(self):
        call_date = self.cleaned_data.get('call_date')
        if call_date and call_date > date.today():
            raise ValidationError(_("Call date cannot be in the future"))
        return call_date
    
    def clean_call_duration_minutes(self):
        duration = self.cleaned_data.get('call_duration_minutes')
        if duration is not None and duration < 0:
            raise ValidationError(_("Call duration cannot be negative"))
        if duration is not None and duration > 1440:  # 24 hours
            raise ValidationError(_("Call duration cannot exceed 24 hours"))
        return duration


class CallAttendanceConfigForm(forms.ModelForm):
    """Form for attendance configuration"""
    
    class Meta:
        model = CallAttendanceConfig
        fields = [
            'full_day_minutes', 'half_day_minutes', 
            'absent_threshold_minutes', 'is_active'
        ]
        widgets = {
            'full_day_minutes': forms.NumberInput(attrs={'min': 1}),
            'half_day_minutes': forms.NumberInput(attrs={'min': 1}),
            'absent_threshold_minutes': forms.NumberInput(attrs={'min': 0}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        full_day = cleaned_data.get('full_day_minutes')
        half_day = cleaned_data.get('half_day_minutes')
        absent_threshold = cleaned_data.get('absent_threshold_minutes')
        
        if full_day and half_day and full_day <= half_day:
            raise ValidationError({
                'full_day_minutes': _("Full day minutes must be greater than half day minutes")
            })
        
        if half_day and absent_threshold and half_day <= absent_threshold:
            raise ValidationError({
                'half_day_minutes': _("Half day minutes must be greater than absent threshold")
            })
        
        return cleaned_data


class ManualAttendanceUpdateForm(forms.Form):
    """Form for manual attendance updates by TL/Manager"""
    
    employee_id = forms.ModelChoiceField(
        queryset=Employee.objects.filter(is_active=True),
        label=_("Employee"),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    attendance_date = forms.DateField(
        label=_("Attendance Date"),
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    call_duration_minutes = forms.IntegerField(
        min_value=0,
        max_value=1440,
        label=_("Call Duration (Minutes)"),
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    call_count = forms.IntegerField(
        min_value=0,
        label=_("Call Count"),
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    def clean_attendance_date(self):
        attendance_date = self.cleaned_data.get('attendance_date')
        if attendance_date and attendance_date > date.today():
            raise ValidationError(_("Attendance date cannot be in the future"))
        return attendance_date


class CallLogBulkUploadForm(forms.Form):
    """Form for bulk uploading call logs"""
    
    csv_file = forms.FileField(
        label=_("CSV File"),
        help_text=_("Upload CSV with columns: employee_id, call_date, call_duration_minutes, call_count"),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv'
        })
    )
    
    def clean_csv_file(self):
        csv_file = self.cleaned_data.get('csv_file')
        if csv_file:
            if not csv_file.name.endswith('.csv'):
                raise ValidationError(_("Please upload a CSV file"))
            if csv_file.size > 5 * 1024 * 1024:  # 5MB limit
                raise ValidationError(_("File size cannot exceed 5MB"))
        return csv_file


class AttendanceFilterForm(forms.Form):
    """Form for filtering attendance records"""
    
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.filter(is_active=True),
        required=False,
        label=_("Employee"),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    start_date = forms.DateField(
        required=False,
        label=_("Start Date"),
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    end_date = forms.DateField(
        required=False,
        label=_("End Date"),
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    status = forms.ChoiceField(
        choices=[('', _('All Status'))] + CallAttendance.ATTENDANCE_STATUS_CHOICES,
        required=False,
        label=_("Attendance Status"),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    source = forms.ChoiceField(
        choices=[('', _('All Sources'))] + CallAttendance.SOURCE_CHOICES,
        required=False,
        label=_("Source"),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise ValidationError({
                'end_date': _("End date must be after start date")
            })
        
        return cleaned_data


class CallAttendanceSearchForm(forms.Form):
    """Simple search form for call attendance"""
    
    search = forms.CharField(
        max_length=100,
        required=False,
        label=_("Search"),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _("Search by employee name...")
        })
    )
    date_from = forms.DateField(
        required=False,
        label=_("From Date"),
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    date_to = forms.DateField(
        required=False,
        label=_("To Date"),
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )