from django.contrib import admin
from .models import ExpenseCategory, Expense, ReimbursementRequest

@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']
    list_filter = ['is_active']

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['title', 'employee', 'category', 'amount', 'status', 'expense_date']
    list_filter = ['status', 'category', 'expense_date']
    search_fields = ['title', 'employee__employee_first_name', 'employee__employee_last_name']

@admin.register(ReimbursementRequest)
class ReimbursementRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'employee', 'total_amount', 'status', 'request_date']
    list_filter = ['status', 'request_date']