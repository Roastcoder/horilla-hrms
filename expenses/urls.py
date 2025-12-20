from django.urls import path
from . import views

urlpatterns = [
    # Employee views
    path('', views.expense_list, name='expense-list'),
    path('create/', views.expense_create, name='expense-create'),
    path('update/<int:pk>/', views.expense_update, name='expense-update'),
    path('submit/<int:pk>/', views.expense_submit, name='expense-submit'),
    
    # Reimbursement views
    path('reimbursements/', views.reimbursement_list, name='reimbursement-list'),
    path('reimbursements/create/', views.reimbursement_create, name='reimbursement-create'),
    
    # Admin views
    path('admin/expenses/', views.admin_expense_list, name='admin-expense-list'),
    path('admin/expenses/<int:pk>/approve/', views.expense_approve, name='expense-approve'),
    path('admin/reimbursements/', views.admin_reimbursement_list, name='admin-reimbursement-list'),
    path('admin/reimbursements/<int:pk>/approve/', views.reimbursement_approve, name='reimbursement-approve'),
]