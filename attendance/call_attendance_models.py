"""
Call-based Auto Attendance Models

This module contains models for implementing call-based automatic attendance
calculation without dependency on external calling platforms.
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import date

from base.horilla_company_manager import HorillaCompanyManager
from base.models import validate_time_format
from employee.models import Employee
from horilla.models import HorillaModel
from horilla_audit.models import HorillaAuditInfo, HorillaAuditLog


class CallLog(HorillaModel):
    """
    Store call data for attendance calculation
    """
    employee_id = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="call_logs",
        verbose_name=_("Employee"),
    )
    call_date = models.DateField(
        verbose_name=_("Call Date"),
        help_text=_("Date when calls were made")
    )
    call_duration_minutes = models.PositiveIntegerField(
        verbose_name=_("Call Duration (Minutes)"),
        help_text=_("Total call duration in minutes")
    )
    call_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Call Count"),
        help_text=_("Total number of calls made")
    )
    source = models.CharField(
        max_length=50,
        default="MANUAL",
        verbose_name=_("Data Source"),
        help_text=_("Source of call data (MANUAL, API, etc.)")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = HorillaCompanyManager(
        related_company_field="employee_id__employee_work_info__company_id"
    )

    class Meta:
        unique_together = ("employee_id", "call_date")
        verbose_name = _("Call Log")
        verbose_name_plural = _("Call Logs")
        ordering = ["-call_date", "employee_id__employee_first_name"]

    def __str__(self):
        return f"{self.employee_id} - {self.call_date} - {self.call_duration_minutes}min"


class CallAttendanceConfig(HorillaModel):
    """
    Configuration for call-based attendance thresholds
    """
    full_day_minutes = models.PositiveIntegerField(
        default=171,
        verbose_name=_("Full Day Minutes"),
        help_text=_("Minimum minutes for full day attendance")
    )
    half_day_minutes = models.PositiveIntegerField(
        default=121,
        verbose_name=_("Half Day Minutes"),
        help_text=_("Minimum minutes for half day attendance")
    )
    absent_threshold_minutes = models.PositiveIntegerField(
        default=120,
        verbose_name=_("Absent Threshold Minutes"),
        help_text=_("Minutes below which employee is marked absent")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active Configuration")
    )
    
    objects = HorillaCompanyManager()

    class Meta:
        verbose_name = _("Call Attendance Configuration")
        verbose_name_plural = _("Call Attendance Configurations")

    def clean(self):
        super().clean()
        if self.full_day_minutes <= self.half_day_minutes:
            raise ValidationError({
                'full_day_minutes': _("Full day minutes must be greater than half day minutes")
            })
        if self.half_day_minutes <= self.absent_threshold_minutes:
            raise ValidationError({
                'half_day_minutes': _("Half day minutes must be greater than absent threshold")
            })

    def save(self, *args, **kwargs):
        if self.is_active:
            # Ensure only one active configuration
            CallAttendanceConfig.objects.filter(is_active=True).update(is_active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Config: {self.full_day_minutes}/{self.half_day_minutes}/{self.absent_threshold_minutes}"


class CallAttendance(HorillaModel):
    """
    Call-based attendance records
    """
    ATTENDANCE_STATUS_CHOICES = [
        ('PRESENT', _('Present')),
        ('HALF_DAY', _('Half Day')),
        ('ABSENT', _('Absent')),
    ]
    
    SOURCE_CHOICES = [
        ('AUTO', _('Auto Calculated')),
        ('MANUAL', _('Manual Override')),
    ]

    employee_id = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="call_attendances",
        verbose_name=_("Employee"),
    )
    attendance_date = models.DateField(
        verbose_name=_("Attendance Date")
    )
    call_duration_minutes = models.PositiveIntegerField(
        verbose_name=_("Call Duration (Minutes)")
    )
    call_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Call Count")
    )
    attendance_status = models.CharField(
        max_length=10,
        choices=ATTENDANCE_STATUS_CHOICES,
        verbose_name=_("Attendance Status")
    )
    source = models.CharField(
        max_length=10,
        choices=SOURCE_CHOICES,
        default='AUTO',
        verbose_name=_("Source")
    )
    manual_reason = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Manual Update Reason"),
        help_text=_("Required when manually updating attendance")
    )
    updated_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="updated_call_attendances",
        verbose_name=_("Updated By")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = HorillaCompanyManager(
        related_company_field="employee_id__employee_work_info__company_id"
    )
    
    history = HorillaAuditLog(
        related_name="history_set",
        bases=[HorillaAuditInfo],
    )

    class Meta:
        unique_together = ("employee_id", "attendance_date")
        verbose_name = _("Call Attendance")
        verbose_name_plural = _("Call Attendances")
        ordering = ["-attendance_date", "employee_id__employee_first_name"]
        permissions = [
            ("manual_update_call_attendance", "Can manually update call attendance"),
        ]

    def clean(self):
        super().clean()
        if self.source == 'MANUAL' and not self.manual_reason:
            raise ValidationError({
                'manual_reason': _("Reason is required for manual updates")
            })

    def __str__(self):
        return f"{self.employee_id} - {self.attendance_date} - {self.attendance_status}"


class CallAttendanceAudit(HorillaModel):
    """
    Audit trail for call attendance manual updates
    """
    call_attendance = models.ForeignKey(
        CallAttendance,
        on_delete=models.CASCADE,
        related_name="audit_logs",
        verbose_name=_("Call Attendance")
    )
    employee_id = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        verbose_name=_("Employee")
    )
    attendance_date = models.DateField(
        verbose_name=_("Attendance Date")
    )
    
    # Old values
    old_call_duration = models.PositiveIntegerField(
        verbose_name=_("Old Call Duration")
    )
    old_call_count = models.PositiveIntegerField(
        verbose_name=_("Old Call Count")
    )
    old_status = models.CharField(
        max_length=10,
        verbose_name=_("Old Status")
    )
    
    # New values
    new_call_duration = models.PositiveIntegerField(
        verbose_name=_("New Call Duration")
    )
    new_call_count = models.PositiveIntegerField(
        verbose_name=_("New Call Count")
    )
    new_status = models.CharField(
        max_length=10,
        verbose_name=_("New Status")
    )
    
    reason = models.TextField(
        verbose_name=_("Update Reason")
    )
    updated_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="audit_updates",
        verbose_name=_("Updated By")
    )
    timestamp = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("Update Timestamp")
    )
    
    objects = HorillaCompanyManager(
        related_company_field="employee_id__employee_work_info__company_id"
    )

    class Meta:
        verbose_name = _("Call Attendance Audit")
        verbose_name_plural = _("Call Attendance Audits")
        ordering = ["-timestamp"]

    def __str__(self):
        return f"Audit: {self.employee_id} - {self.attendance_date} by {self.updated_by}"