"""
Sales Incentive Models
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
    min_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Min Amount (Lac)"))
    max_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name=_("Max Amount (Lac)"))
    incentive_per_lac = models.DecimalField(max_digits=8, decimal_places=2, verbose_name=_("Incentive per Lac (₹)"))
    is_active = models.BooleanField(default=True)
    
    objects = HorillaCompanyManager()
    
    class Meta:
        verbose_name = _("Incentive Slab")
        ordering = ['min_amount']


class LoanType(HorillaModel):
    name = models.CharField(max_length=100, verbose_name=_("Loan Type"))
    points_per_lac = models.DecimalField(max_digits=5, decimal_places=2, verbose_name=_("Points per Lac"))
    is_active = models.BooleanField(default=True)
    
    objects = HorillaCompanyManager()


class Lead(HorillaModel):
    STATUS_CHOICES = [
        ('NEW', _('New')),
        ('DISBURSED', _('Disbursed')),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="sales_leads")
    loan_type = models.ForeignKey(LoanType, on_delete=models.CASCADE)
    loan_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_("Loan Amount (₹)"))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW')
    disbursed_date = models.DateTimeField(null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    
    objects = HorillaCompanyManager(related_company_field="employee__employee_work_info__company_id")
    
    @property
    def loan_amount_lac(self):
        return self.loan_amount / 100000