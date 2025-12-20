from django.urls import path
from . import views

app_name = 'sales_incentive'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('incentive-slabs/', views.incentive_slab_view, name='incentive-slab-view'),
    path('incentive-slabs/create/', views.incentive_slab_create, name='incentive-slab-create'),
    path('incentive-slabs/update/<int:slab_id>/', views.incentive_slab_update, name='incentive-slab-update'),
    path('incentive-slabs/delete/<int:slab_id>/', views.incentive_slab_delete, name='incentive-slab-delete'),
    path('loan-types/', views.loan_type_view, name='loan-type-view'),
    path('loan-types/create/', views.loan_type_create, name='loan-type-create'),
    path('loan-types/update/<int:type_id>/', views.loan_type_update, name='loan-type-update'),
    path('loan-types/delete/<int:type_id>/', views.loan_type_delete, name='loan-type-delete'),
    path('leads/', views.lead_view, name='lead-view'),
    path('leads/create/', views.lead_create, name='lead-create'),
    path('leads/update/<int:lead_id>/', views.lead_update, name='lead-update'),
    path('leads/delete/<int:lead_id>/', views.lead_delete, name='lead-delete'),
    path('manual-attendance/', views.manual_attendance, name='manual-attendance'),
    path('download-template/', views.download_template, name='download-template'),
    path('upload-attendance/', views.upload_attendance, name='upload-attendance'),
]