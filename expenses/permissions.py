"""
Custom permissions and decorators for expenses module
"""
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from functools import wraps
from .models import Expense, ReimbursementRequest

def can_approve_expenses(user):
    """Check if user can approve expenses"""
    return user.has_perm('expenses.change_expense') or user.is_superuser

def can_manage_expenses(user):
    """Check if user can manage all expenses"""
    return user.has_perm('expenses.view_expense') and user.has_perm('expenses.change_expense')

def expense_owner_required(view_func):
    """Decorator to ensure user owns the expense or has permission to view all"""
    @wraps(view_func)
    def _wrapped_view(request, pk, *args, **kwargs):
        expense = get_object_or_404(Expense, pk=pk)
        
        # Allow if user owns the expense or has permission to view all expenses
        if expense.employee.employee_user_id == request.user or can_manage_expenses(request.user):
            return view_func(request, pk, *args, **kwargs)
        
        raise PermissionDenied("You don't have permission to access this expense.")
    
    return _wrapped_view

def reimbursement_owner_required(view_func):
    """Decorator to ensure user owns the reimbursement request"""
    @wraps(view_func)
    def _wrapped_view(request, pk, *args, **kwargs):
        reimbursement = get_object_or_404(ReimbursementRequest, pk=pk)
        
        if reimbursement.employee.employee_user_id == request.user or can_manage_expenses(request.user):
            return view_func(request, pk, *args, **kwargs)
        
        raise PermissionDenied("You don't have permission to access this reimbursement request.")
    
    return _wrapped_view

# Permission decorators
expense_approver_required = user_passes_test(can_approve_expenses)
expense_manager_required = user_passes_test(can_manage_expenses)