# Complete Working Expenses Module Setup Guide

## 🚀 Quick Setup (5 Minutes)

### Step 1: Add to Settings
Edit `horilla/settings.py`:
```python
INSTALLED_APPS = [
    # ... existing apps ...
    'expenses',  # Add this line
]

# Add media configuration if not present
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

### Step 2: Add URLs
Edit `horilla/urls.py`:
```python
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ... existing patterns ...
    path('expenses/', include('expenses.urls')),  # Add this line
]

# Add this for media files
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

### Step 3: Run Setup Commands
```bash
cd /path/to/horilla
source horillavenv/bin/activate

# Create and run migrations
python manage.py makemigrations expenses
python manage.py migrate

# Set up permissions and roles
python manage.py setup_expense_permissions

# Create expense categories
python manage.py shell
```

In Django shell:
```python
from expenses.models import ExpenseCategory

categories = ['Travel', 'Meals', 'Office Supplies', 'Training', 'Equipment', 'Other']
for cat in categories:
    ExpenseCategory.objects.get_or_create(name=cat)

exit()
```

### Step 4: Assign User Roles
```bash
python manage.py shell
```

```python
from django.contrib.auth.models import User, Group
from employee.models import Employee

# Get groups
expense_managers = Group.objects.get(name='Expense Managers')
expense_approvers = Group.objects.get(name='Expense Approvers')
employees = Group.objects.get(name='Employees')

# Assign roles to users (replace with actual usernames)
# Make HR manager an expense manager
hr_user = User.objects.get(username='hr_manager')
hr_user.groups.add(expense_managers)

# Make department heads expense approvers
dept_head = User.objects.get(username='dept_head')
dept_head.groups.add(expense_approvers)

# Make regular employees part of employees group
regular_user = User.objects.get(username='employee1')
regular_user.groups.add(employees)

exit()
```

## 📋 User Roles & Permissions

### 1. Expense Managers (HR/Finance)
**Permissions:**
- View all expenses
- Approve/reject expenses
- Manage expense categories
- View/approve reimbursement requests
- Access admin interfaces

**Access:**
- `/expenses/admin/expenses/` - Approve expenses
- `/expenses/admin/reimbursements/` - Manage reimbursements
- Django admin for full management

### 2. Expense Approvers (Department Heads)
**Permissions:**
- View submitted expenses
- Approve/reject expenses
- View reimbursement requests
- Approve reimbursements

**Access:**
- `/expenses/admin/expenses/` - Approve expenses
- `/expenses/admin/reimbursements/` - Approve reimbursements

### 3. Employees (Regular Users)
**Permissions:**
- Create own expenses
- View own expenses
- Submit expenses for approval
- Create reimbursement requests
- View own reimbursement status

**Access:**
- `/expenses/` - My expenses
- `/expenses/create/` - Add expense
- `/expenses/reimbursements/` - My reimbursements

## 🔗 Complete URL Structure

```
Employee URLs:
/expenses/                              # My expenses list
/expenses/create/                       # Add new expense
/expenses/update/<id>/                  # Edit expense (draft only)
/expenses/submit/<id>/                  # Submit for approval
/expenses/reimbursements/               # My reimbursement requests
/expenses/reimbursements/create/        # Request reimbursement

Manager URLs:
/expenses/admin/expenses/               # Pending expense approvals
/expenses/admin/expenses/<id>/approve/  # Approve/reject expense
/expenses/admin/reimbursements/         # Reimbursement approvals
/expenses/admin/reimbursements/<id>/approve/  # Approve reimbursement

Django Admin:
/admin/expenses/expense/                # Full expense management
/admin/expenses/expensecategory/        # Category management
/admin/expenses/reimbursementrequest/   # Reimbursement management
```

## 🔄 Complete Workflow

### Employee Workflow:
1. **Create Expense** → Status: `draft`
2. **Edit/Update** → Still `draft`
3. **Submit** → Status: `submitted`
4. **Wait for Approval** → Status: `approved`/`rejected`
5. **Request Reimbursement** → Select approved expenses
6. **Track Reimbursement** → Status: `pending`/`approved`/`paid`

### Manager Workflow:
1. **Review Submitted Expenses** → `/expenses/admin/expenses/`
2. **Approve/Reject** → Add reason if rejecting
3. **Review Reimbursement Requests** → `/expenses/admin/reimbursements/`
4. **Approve Reimbursement** → Ready for payment
5. **Mark as Paid** → Complete process

## 🛠 File Structure Summary

```
expenses/
├── __init__.py
├── apps.py
├── models.py                    # Expense, ExpenseCategory, ReimbursementRequest
├── views.py                     # All CRUD operations with permissions
├── forms.py                     # Django forms
├── urls.py                      # URL patterns
├── admin.py                     # Django admin
├── permissions.py               # Custom permission decorators
├── management/
│   └── commands/
│       └── setup_expense_permissions.py
├── migrations/
│   ├── __init__.py
│   └── 0001_initial.py
└── templates/expenses/
    ├── expense_list.html
    ├── expense_form.html
    ├── reimbursement_list.html
    ├── reimbursement_form.html
    ├── admin_expense_list.html
    └── admin_reimbursement_list.html
```

## ✅ Testing the Setup

### 1. Test Employee Functions:
```bash
# Login as regular employee
# Navigate to: http://localhost:8000/expenses/
# Should see: My Expenses page with "Add Expense" button
```

### 2. Test Manager Functions:
```bash
# Login as manager/approver
# Navigate to: http://localhost:8000/expenses/admin/expenses/
# Should see: Pending expense approvals
```

### 3. Test Permissions:
```bash
# Regular employee trying to access admin URLs should get 403 Forbidden
# Managers should see admin interfaces
```

## 🔧 Troubleshooting

**Issue: Module not found**
```bash
# Ensure expenses is in INSTALLED_APPS
# Restart Django server
python manage.py runserver
```

**Issue: Permission denied**
```bash
# Run permission setup command
python manage.py setup_expense_permissions

# Assign users to groups
python manage.py shell
>>> from django.contrib.auth.models import User, Group
>>> user = User.objects.get(username='your_username')
>>> group = Group.objects.get(name='Employees')
>>> user.groups.add(group)
```

**Issue: No categories available**
```bash
# Create categories via shell or admin
python manage.py shell
>>> from expenses.models import ExpenseCategory
>>> ExpenseCategory.objects.create(name='Travel')
```

This setup provides a complete, working expenses module with proper roles, permissions, and workflow integration into Horilla HRMS.