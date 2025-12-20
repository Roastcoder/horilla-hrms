from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum
from django.utils import timezone
from .models import Expense, ExpenseCategory, ReimbursementRequest
from .forms import ExpenseForm, ExpenseCategoryForm, ReimbursementRequestForm
from .permissions import (
    expense_owner_required, 
    expense_approver_required, 
    expense_manager_required,
    reimbursement_owner_required
)

@login_required
def expense_list(request):
    expenses = Expense.objects.filter(employee=request.user.employee_get)
    return render(request, 'expenses/expense_list.html', {'expenses': expenses})

@login_required
def expense_create(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST, request.FILES)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.employee = request.user.employee_get
            expense.save()
            messages.success(request, 'Expense created successfully!')
            return redirect('expense-list')
    else:
        form = ExpenseForm()
    return render(request, 'expenses/expense_form.html', {'form': form})

@login_required
@expense_owner_required
def expense_update(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    
    # Only allow editing if user owns expense and it's in draft status
    if expense.employee.employee_user_id != request.user:
        messages.error(request, 'You can only edit your own expenses.')
        return redirect('expense-list')
    
    if expense.status != 'draft':
        messages.error(request, 'Cannot edit submitted expense.')
        return redirect('expense-list')
    
    if request.method == 'POST':
        form = ExpenseForm(request.POST, request.FILES, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, 'Expense updated successfully!')
            return redirect('expense-list')
    else:
        form = ExpenseForm(instance=expense)
    return render(request, 'expenses/expense_form.html', {'form': form, 'expense': expense})

@login_required
@expense_owner_required
def expense_submit(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    
    if expense.employee.employee_user_id != request.user:
        messages.error(request, 'You can only submit your own expenses.')
        return redirect('expense-list')
    
    if expense.status == 'draft':
        expense.status = 'submitted'
        expense.save()
        messages.success(request, 'Expense submitted for approval!')
    return redirect('expense-list')

@login_required
def reimbursement_list(request):
    requests = ReimbursementRequest.objects.filter(employee=request.user.employee_get).prefetch_related('expenses')
    return render(request, 'expenses/reimbursement_list.html', {'requests': requests})

@login_required
def reimbursement_create(request):
    if request.method == 'POST':
        form = ReimbursementRequestForm(request.POST, employee=request.user.employee_get)
        if form.is_valid():
            selected_expenses = form.cleaned_data['expenses']
            
            # Validate that all expenses belong to the user
            user_expenses = selected_expenses.filter(employee=request.user.employee_get)
            if user_expenses.count() != selected_expenses.count():
                messages.error(request, 'You can only request reimbursement for your own expenses.')
                return render(request, 'expenses/reimbursement_form.html', {'form': form})
            
            reimbursement = form.save(commit=False)
            reimbursement.employee = request.user.employee_get
            reimbursement.total_amount = selected_expenses.aggregate(Sum('amount'))['amount__sum'] or 0
            reimbursement.save()
            reimbursement.expenses.set(selected_expenses)
            messages.success(request, 'Reimbursement request created successfully!')
            return redirect('reimbursement-list')
    else:
        form = ReimbursementRequestForm(employee=request.user.employee_get)
    return render(request, 'expenses/reimbursement_form.html', {'form': form})

# Admin views
@login_required
@expense_approver_required
def expense_approve(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            expense.status = 'approved'
            expense.approved_by = request.user
            expense.approved_at = timezone.now()
            messages.success(request, 'Expense approved!')
        elif action == 'reject':
            expense.status = 'rejected'
            expense.rejection_reason = request.POST.get('reason', '')
            messages.success(request, 'Expense rejected!')
        expense.save()
    return redirect('admin-expense-list')

@login_required
@expense_manager_required
def admin_expense_list(request):
    expenses = Expense.objects.filter(status='submitted').select_related('employee', 'category')
    return render(request, 'expenses/admin_expense_list.html', {'expenses': expenses})

@login_required
@expense_manager_required
def reimbursement_approve(request, pk):
    reimbursement = get_object_or_404(ReimbursementRequest, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            reimbursement.status = 'approved'
            reimbursement.approved_by = request.user
            reimbursement.approved_at = timezone.now()
            messages.success(request, 'Reimbursement approved!')
        elif action == 'reject':
            reimbursement.status = 'rejected'
            messages.success(request, 'Reimbursement rejected!')
        elif action == 'pay':
            reimbursement.status = 'paid'
            messages.success(request, 'Reimbursement marked as paid!')
        reimbursement.save()
    return redirect('admin-reimbursement-list')

@login_required
@expense_manager_required
def admin_reimbursement_list(request):
    requests = ReimbursementRequest.objects.filter(status__in=['pending', 'approved']).select_related('employee')
    return render(request, 'expenses/admin_reimbursement_list.html', {'requests': requests})