"""
Sales Incentive URL Configuration
"""

from django.urls import path
from . import sales_incentive_views as views

app_name = 'sales_incentive'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.sales_dashboard, name='dashboard'),
    
    # Incentive Slabs
    path('slabs/', views.incentive_slab_list, name='slab_list'),
    path('slabs/create/', views.incentive_slab_create, name='slab_create'),
    path('slabs/<int:pk>/edit/', views.incentive_slab_edit, name='slab_edit'),
    
    # Loan Types
    path('loan-types/', views.loan_type_list, name='loan_type_list'),
    path('loan-types/create/', views.loan_type_create, name='loan_type_create'),
    path('loan-types/<int:pk>/edit/', views.loan_type_edit, name='loan_type_edit'),
    
    # Leads
    path('leads/', views.lead_list, name='lead_list'),
    path('leads/create/', views.lead_create, name='lead_create'),
    path('leads/<int:pk>/edit/', views.lead_edit, name='lead_edit'),
    
    # Targets
    path('targets/', views.target_list, name='target_list'),
    path('targets/create/', views.target_create, name='target_create'),
    path('targets/<int:pk>/edit/', views.target_edit, name='target_edit'),
    
    # Incentive Calculations
    path('calculations/', views.incentive_calculation_list, name='calculation_list'),
    path('calculations/bulk/', views.bulk_incentive_calculation, name='bulk_calculation'),
    
    # Reports
    path('reports/', views.reports, name='reports'),
    
    # Call Configuration
    path('call-config/', views.call_config, name='call_config'),
]