"""
Sales Incentive Views

Views for managing sales incentives, targets, and performance tracking.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Q
from django.http import JsonResponse, HttpResponse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from datetime import date, datetime
import json

from employee.models import Employee
from .sales_incentive_models import (
    IncentiveSlab, LoanType, SalesTarget, Lead, 
    IncentiveCalculation, CallAttendanceConfig
)
from .sales_incentive_forms import (
    IncentiveSlabForm, LoanTypeForm, SalesTargetForm, LeadForm,
    IncentiveCalculationForm, CallAttendanceConfigForm,
    BulkIncentiveCalculationForm, ReportFilterForm
)


@login_required
@permission_required('sales.view_incentiveslab')
def incentive_slab_list(request):
    """List all incentive slabs"""
    slabs = IncentiveSlab.objects.all().order_by('min_amount')
    
    context = {
        'slabs': slabs,
        'page_title': _('Incentive Slabs')
    }
    return render(request, 'sales_incentive/slab_list.html', context)


@login_required
@permission_required('sales.add_incentiveslab')
def incentive_slab_create(request):
    """Create new incentive slab"""
    if request.method == 'POST':
        form = IncentiveSlabForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('Incentive slab created successfully'))
            return redirect('incentive_slab_list')
    else:
        form = IncentiveSlabForm()
    
    return render(request, 'sales_incentive/slab_form.html', {'form': form})


@login_required
@permission_required('sales.change_incentiveslab')
def incentive_slab_edit(request, pk):
    """Edit incentive slab"""
    slab = get_object_or_404(IncentiveSlab, pk=pk)
    
    if request.method == 'POST':
        form = IncentiveSlabForm(request.POST, instance=slab)
        if form.is_valid():
            form.save()
            messages.success(request, _('Incentive slab updated successfully'))
            return redirect('incentive_slab_list')
    else:
        form = IncentiveSlabForm(instance=slab)
    
    return render(request, 'sales_incentive/slab_form.html', {'form': form, 'slab': slab})


@login_required
@permission_required('sales.view_lead')
def lead_list(request):
    """List all leads with filtering"""
    leads = Lead.objects.select_related('employee', 'loan_type').order_by('-created_date')
    
    # Filtering
    status = request.GET.get('status')
    employee_id = request.GET.get('employee')
    loan_type_id = request.GET.get('loan_type')
    
    if status:
        leads = leads.filter(status=status)
    if employee_id:
        leads = leads.filter(employee_id=employee_id)
    if loan_type_id:
        leads = leads.filter(loan_type_id=loan_type_id)
    
    # Pagination
    paginator = Paginator(leads, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'employees': Employee.objects.filter(is_active=True),
        'loan_types': LoanType.objects.filter(is_active=True),
        'status_choices': Lead.STATUS_CHOICES,
        'filters': {
            'status': status,
            'employee': employee_id,
            'loan_type': loan_type_id,
        }
    }
    return render(request, 'sales_incentive/lead_list.html', context)


@login_required
@permission_required('sales.add_lead')
def lead_create(request):
    """Create new lead"""
    if request.method == 'POST':
        form = LeadForm(request.POST)
        if form.is_valid():
            lead = form.save()
            messages.success(request, _('Lead created successfully'))
            return redirect('lead_list')
    else:
        form = LeadForm()
    
    return render(request, 'sales_incentive/lead_form.html', {'form': form})


@login_required
@permission_required('sales.change_lead')
def lead_edit(request, pk):
    """Edit lead"""
    lead = get_object_or_404(Lead, pk=pk)
    
    if request.method == 'POST':
        form = LeadForm(request.POST, instance=lead)
        if form.is_valid():
            form.save()
            messages.success(request, _('Lead updated successfully'))
            return redirect('lead_list')
    else:
        form = LeadForm(instance=lead)
    
    return render(request, 'sales_incentive/lead_form.html', {'form': form, 'lead': lead})


@login_required
@permission_required('sales.view_salestaget')
def target_list(request):
    """List sales targets"""
    targets = SalesTarget.objects.select_related('employee').order_by('-month')
    
    # Filtering
    month = request.GET.get('month')
    employee_id = request.GET.get('employee')
    
    if month:
        targets = targets.filter(month__year=int(month[:4]), month__month=int(month[5:]))
    if employee_id:
        targets = targets.filter(employee_id=employee_id)
    
    paginator = Paginator(targets, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'employees': Employee.objects.filter(is_active=True),
        'filters': {
            'month': month,
            'employee': employee_id,
        }
    }
    return render(request, 'sales_incentive/target_list.html', context)


@login_required
@permission_required('sales.add_salestaget')
def target_create(request):
    """Create sales target"""
    if request.method == 'POST':
        form = SalesTargetForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('Sales target created successfully'))
            return redirect('target_list')
    else:
        form = SalesTargetForm()
    
    return render(request, 'sales_incentive/target_form.html', {'form': form})


@login_required
@permission_required('sales.view_incentivecalculation')
def incentive_calculation_list(request):
    """List incentive calculations"""
    calculations = IncentiveCalculation.objects.select_related('employee').order_by('-month')
    
    paginator = Paginator(calculations, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'sales_incentive/calculation_list.html', context)


@login_required
@permission_required('sales.add_incentivecalculation')
def bulk_incentive_calculation(request):
    """Bulk calculate incentives"""
    if request.method == 'POST':
        form = BulkIncentiveCalculationForm(request.POST)
        if form.is_valid():
            month = form.cleaned_data['month']
            employees = form.cleaned_data['employees']
            recalculate = form.cleaned_data['recalculate']
            
            if not employees:
                employees = Employee.objects.filter(is_active=True)
            
            calculated_count = 0
            for employee in employees:
                calculation, created = IncentiveCalculation.objects.get_or_create(
                    employee=employee,
                    month=month,
                    defaults={'waiver_percentage': 30}
                )
                
                if created or recalculate:
                    calculation.calculate_incentive()
                    calculated_count += 1
            
            messages.success(request, 
                f'Calculated incentives for {calculated_count} employees')
            return redirect('incentive_calculation_list')
    else:
        form = BulkIncentiveCalculationForm()
    
    return render(request, 'sales_incentive/bulk_calculation.html', {'form': form})


@login_required
def sales_dashboard(request):
    """Sales performance dashboard"""
    today = date.today()
    current_month = today.replace(day=1)
    
    # Current month statistics
    current_leads = Lead.objects.filter(
        created_date__year=today.year,
        created_date__month=today.month
    )
    
    stats = {
        'total_leads': current_leads.count(),
        'disbursed_leads': current_leads.filter(status='DISBURSED').count(),
        'total_amount': current_leads.filter(status='DISBURSED').aggregate(
            total=Sum('loan_amount'))['total'] or 0,
        'total_points': sum(lead.points_earned for lead in current_leads.filter(status='DISBURSED')),
    }
    
    # Top performers
    top_performers = IncentiveCalculation.objects.filter(
        month=current_month
    ).order_by('-final_incentive')[:5]
    
    # Recent leads
    recent_leads = Lead.objects.select_related('employee', 'loan_type').order_by('-created_date')[:10]
    
    context = {
        'stats': stats,
        'top_performers': top_performers,
        'recent_leads': recent_leads,
    }
    
    return render(request, 'sales_incentive/dashboard.html', context)


@login_required
def reports(request):
    """Generate various reports"""
    if request.method == 'POST':
        form = ReportFilterForm(request.POST)
        if form.is_valid():
            report_type = form.cleaned_data['report_type']
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            employees = form.cleaned_data['employees']
            
            if not employees:
                employees = Employee.objects.filter(is_active=True)
            
            context = {
                'report_type': report_type,
                'start_date': start_date,
                'end_date': end_date,
                'employees': employees,
            }
            
            if report_type == 'incentive':
                calculations = IncentiveCalculation.objects.filter(
                    employee__in=employees,
                    month__range=[start_date, end_date]
                ).select_related('employee')
                context['calculations'] = calculations
                
            elif report_type == 'target_achievement':
                targets = SalesTarget.objects.filter(
                    employee__in=employees,
                    month__range=[start_date, end_date]
                ).select_related('employee')
                
                # Add achievement data
                for target in targets:
                    disbursed_amount = Lead.objects.filter(
                        employee=target.employee,
                        status='DISBURSED',
                        disbursed_date__year=target.month.year,
                        disbursed_date__month=target.month.month
                    ).aggregate(total=Sum('loan_amount'))['total'] or 0
                    
                    target.achieved_amount = disbursed_amount / 100000  # Convert to Lac
                    target.achievement_percentage = (
                        (target.achieved_amount / target.final_target_amount * 100) 
                        if target.final_target_amount > 0 else 0
                    )
                
                context['targets'] = targets
            
            return render(request, 'sales_incentive/report_results.html', context)
    else:
        form = ReportFilterForm()
    
    return render(request, 'sales_incentive/reports.html', {'form': form})


@login_required
@permission_required('sales.view_callattendanceconfig')
def call_config(request):
    """Manage call attendance configuration"""
    config = CallAttendanceConfig.objects.filter(is_active=True).first()
    
    if request.method == 'POST':
        if config:
            form = CallAttendanceConfigForm(request.POST, instance=config)
        else:
            form = CallAttendanceConfigForm(request.POST)
        
        if form.is_valid():
            if config:
                # Deactivate old config
                config.is_active = False
                config.save()
            
            new_config = form.save()
            messages.success(request, _('Call attendance configuration updated'))
            return redirect('call_config')
    else:
        form = CallAttendanceConfigForm(instance=config)
    
    return render(request, 'sales_incentive/call_config.html', {'form': form, 'config': config})