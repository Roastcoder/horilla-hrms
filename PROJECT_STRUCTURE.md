# Complete Horilla HRMS Project Structure with Expenses Module

## 📁 Project File Structure

```
horilla-1.0/
├── horilla/                           # Main project directory
│   ├── __init__.py
│   ├── settings.py                    # ✅ UPDATED - Add expenses app
│   ├── urls.py                        # ✅ UPDATED - Add expenses URLs
│   └── wsgi.py
├── employee/                          # Employee management
│   ├── models.py
│   ├── views.py
│   └── ...
├── base/                             # Base configurations
│   ├── models.py
│   ├── views.py
│   └── ...
├── expenses/                         # ✅ NEW MODULE
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py                     # Expense, ExpenseCategory, ReimbursementRequest
│   ├── views.py                      # CRUD operations, approvals
│   ├── forms.py                      # Django forms
│   ├── urls.py                       # URL patterns
│   ├── admin.py                      # Admin interface
│   ├── permissions.py                # ✅ NEW - Custom permissions
│   ├── decorators.py                 # ✅ NEW - Permission decorators
│   ├── migrations/
│   │   ├── __init__.py
│   │   └── 0001_initial.py
│   ├── templates/expenses/
│   │   ├── expense_list.html
│   │   ├── expense_form.html
│   │   ├── reimbursement_list.html
│   │   ├── reimbursement_form.html
│   │   └── admin_expense_list.html
│   └── static/expenses/
│       ├── css/
│       └── js/
├── media/                            # File uploads
│   └── expenses/
│       └── receipts/
├── manage.py
└── requirements.txt
```

## 🔧 Complete Implementation Files

### 1. Updated Settings (horilla/settings.py)
```python
# Add to INSTALLED_APPS
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Horilla apps
    'base',
    'employee',
    'attendance',
    'leave',
    'payroll',
    
    # New module
    'expenses',  # ✅ ADD THIS
]

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

### 2. Updated URLs (horilla/urls.py)
```python
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('base.urls')),
    path('employee/', include('employee.urls')),
    path('expenses/', include('expenses.urls')),  # ✅ ADD THIS
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```