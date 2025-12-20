"""
Sales Incentive and Performance Management Models

This module contains models for managing sales team incentives, targets, 
and performance tracking in Horilla HRMS.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from decimal import Decimal

from base.horilla_company_manager import HorillaCompanyManager
from employee.models import Employee
from horilla.models import HorillaModel
from horilla_audit.models import HorillaAuditInfo, HorillaAuditLog


class IncentiveSlab(HorillaModel):
    """Admin-configurable incentive slabs based on loan amount"""
    
    min_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name=_("Minimum Amount (Lac)"),
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    max_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name=_("Maximum Amount (Lac)"),
        null=True, blank=True,
        help_text=_("Leave blank for unlimited upper limit")
    )
    incentive_per_lac = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name=_("Incentive per Lac (₹)"),
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))
    
    objects = HorillaCompanyManager()
    
    class Meta:
        verbose_name = _("Incentive Slab")
        verbose_name_plural = _("Incentive Slabs")
        ordering = ['min_amount']
    
    def __str__(self):
        max_display = f"{self.max_amount}" if self.max_amount else "∞"
        return f"{self.min_amount}-{max_display} Lac → ₹{self.incentive_per_lac}/Lac"


class LoanType(HorillaModel):
    """Configurable loan types with point calculation"""
    
    name = models.CharField(max_length=100, verbose_name=_("Loan Type"))
    points_per_lac = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name=_("Points per Lac"),
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))
    
    objects = HorillaCompanyManager()
    
    class Meta:
        verbose_name = _("Loan Type")
        verbose_name_plural = _("Loan Types")
    
    def __str__(self):
        return f"{self.name} ({self.points_per_lac} pts/Lac)"


class SalesTarget(HorillaModel):
    """Employee sales targets"""
    
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="sales_targets",
        verbose_name=_("Employee")
    )
    month = models.DateField(verbose_name=_("Target Month"))
    target_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Target Amount (Lac)"),
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    auto_target_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Auto Target (Based on Salary)"),
        null=True, blank=True
    )
    final_target_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Final Target Amount"),
        help_text=_("Higher of manual or auto target")
    )
    
    objects = HorillaCompanyManager(
        related_company_field="employee__employee_work_info__company_id"
    )
    
    class Meta:
        verbose_name = _("Sales Target")
        verbose_name_plural = _("Sales Targets")
        unique_together = ['employee', 'month']
    
    def save(self, *args, **kwargs):
        # Calculate auto target based on salary
        if self.employee.employee_work_info and self.employee.employee_work_info.basic_salary:
            self.auto_target_amount = self.employee.employee_work_info.basic_salary / 1000
        
        # Set final target as higher of manual or auto
        self.final_target_amount = max(
            self.target_amount or 0,
            self.auto_target_amount or 0
        )
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.employee} - {self.month.strftime('%b %Y')} - ₹{self.final_target_amount}L"


class Lead(HorillaModel):
    """Lead/Application tracking"""
    
    STATUS_CHOICES = [
        ('NEW', _('New')),
        ('IN_PROGRESS', _('In Progress')),
        ('APPROVED', _('Approved')),
        ('REJECTED', _('Rejected')),
        ('DISBURSED', _('Disbursed')),
    ]
    
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="leads",
        verbose_name=_("Sales Person")
    )
    loan_type = models.ForeignKey(
        LoanType,
        on_delete=models.CASCADE,
        verbose_name=_("Loan Type")
    )
    loan_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Loan Amount (₹)"),
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='NEW',
        verbose_name=_("Status")
    )
    
    # KYC/Account flags
    ac_new_api = models.BooleanField(default=False, verbose_name=_("A/C New API"))
    kyc_api = models.BooleanField(default=False, verbose_name=_("KYC API"))
    aip = models.BooleanField(default=False, verbose_name=_("AIP"))
    
    created_date = models.DateTimeField(auto_now_add=True)
    disbursed_date = models.DateTimeField(null=True, blank=True)
    
    objects = HorillaCompanyManager(
        related_company_field="employee__employee_work_info__company_id"
    )
    
    history = HorillaAuditLog(
        related_name="history_set",
        bases=[HorillaAuditInfo],
    )
    
    class Meta:
        verbose_name = _("Lead")
        verbose_name_plural = _("Leads")
    
    @property
    def loan_amount_lac(self):
        """Convert loan amount to Lac"""
        return self.loan_amount / 100000
    
    @property
    def points_earned(self):
        """Calculate points based on loan type"""
        return self.loan_amount_lac * self.loan_type.points_per_lac
    
    def __str__(self):
        return f"{self.employee} - {self.loan_type} - ₹{self.loan_amount_lac}L"


class IncentiveCalculation(HorillaModel):
    """Monthly incentive calculations"""
    
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="incentive_calculations",
        verbose_name=_("Employee")
    )
    month = models.DateField(verbose_name=_("Month"))
    total_disbursed_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name=_("Total Disbursed Amount (₹)")
    )
    total_points = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Total Points")
    )
    incentive_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Incentive Amount (₹)")
    )
    waiver_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=30,
        verbose_name=_("Waiver %"),
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    final_incentive = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Final Incentive (₹)")
    )
    is_calculated = models.BooleanField(default=False)
    calculated_at = models.DateTimeField(null=True, blank=True)
    
    objects = HorillaCompanyManager(
        related_company_field="employee__employee_work_info__company_id"
    )
    
    class Meta:
        verbose_name = _("Incentive Calculation")
        verbose_name_plural = _("Incentive Calculations")
        unique_together = ['employee', 'month']
    
    def calculate_incentive(self):
        """Calculate incentive based on slabs"""
        disbursed_leads = Lead.objects.filter(
            employee=self.employee,
            status='DISBURSED',
            disbursed_date__year=self.month.year,
            disbursed_date__month=self.month.month
        )
        
        self.total_disbursed_amount = sum(lead.loan_amount for lead in disbursed_leads)
        self.total_points = sum(lead.points_earned for lead in disbursed_leads)
        
        # Calculate incentive based on slabs
        amount_lac = self.total_disbursed_amount / 100000
        incentive = 0
        
        slabs = IncentiveSlab.objects.filter(is_active=True).order_by('min_amount')
        
        for slab in slabs:
            if amount_lac >= slab.min_amount:
                if slab.max_amount is None or amount_lac <= slab.max_amount:
                    # Amount falls in this slab
                    slab_amount = min(
                        amount_lac - slab.min_amount + 1,
                        (slab.max_amount - slab.min_amount + 1) if slab.max_amount else amount_lac
                    )
                    incentive += slab_amount * slab.incentive_per_lac
                    amount_lac -= slab_amount
                    if amount_lac <= 0:
                        break
        
        self.incentive_amount = incentive
        self.final_incentive = incentive * (1 - self.waiver_percentage / 100)
        self.is_calculated = True
        self.calculated_at = timezone.now()
        self.save()
    
    def __str__(self):
        return f"{self.employee} - {self.month.strftime('%b %Y')} - ₹{self.final_incentive}"


class CallAttendanceConfig(HorillaModel):
    """Call attendance configuration for telecallers"""
    
    daily_required_minutes = models.PositiveIntegerField(
        default=400,
        verbose_name=_("Daily Required Minutes")
    )
    present_threshold = models.PositiveIntegerField(
        default=171,
        verbose_name=_("Present Threshold (Minutes)")
    )
    half_day_threshold = models.PositiveIntegerField(
        default=121,
        verbose_name=_("Half Day Threshold (Minutes)")
    )
    absent_threshold = models.PositiveIntegerField(
        default=120,
        verbose_name=_("Absent Threshold (Minutes)")
    )
    is_active = models.BooleanField(default=True)
    
    objects = HorillaCompanyManager()
    
    class Meta:
        verbose_name = _("Call Attendance Config")
        verbose_name_plural = _("Call Attendance Configs")
    
    def __str__(self):
        return f"Call Config: {self.daily_required_minutes}min required"