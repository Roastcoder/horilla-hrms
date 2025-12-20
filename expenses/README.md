# Expenses Module for Horilla HRMS

A minimal expense tracking and reimbursement management module for Horilla HRMS.

## Features

- ✅ Add and track expenses
- ✅ Submit expenses for approval
- ✅ Approve/reject expenses (managers)
- ✅ Request reimbursement for approved expenses
- ✅ Upload receipts
- ✅ Expense categories

## Installation

### 1. Add to INSTALLED_APPS

Edit `horilla/settings.py`:

```python
INSTALLED_APPS = [
    # ... existing apps ...
    'expenses',
]
```

### 2. Add URLs

Edit `horilla/urls.py`:

```python
urlpatterns = [
    # ... existing patterns ...
    path('expenses/', include('expenses.urls')),
]
```

### 3. Run Migrations

```bash
cd /path/to/horilla
source horillavenv/bin/activate
python manage.py makemigrations expenses
python manage.py migrate expenses
```

### 4. Create Expense Categories

```bash
python manage.py shell
```

```python
from expenses.models import ExpenseCategory

categories = [
    'Travel',
    'Meals',
    'Office Supplies',
    'Training',
    'Equipment',
    'Other'
]

for cat in categories:
    ExpenseCategory.objects.get_or_create(name=cat)
```

## Usage

### Employee Workflow

1. **Add Expense**: `/expenses/create/`
   - Fill in expense details
   - Upload receipt (optional)
   - Save as draft

2. **Submit for Approval**: Click "Submit" on expense list
   - Changes status to "Submitted"

3. **Request Reimbursement**: `/expenses/reimbursements/create/`
   - Select approved expenses
   - Submit reimbursement request

### Manager Workflow

1. **Review Expenses**: `/expenses/admin/expenses/`
   - View pending expenses
   - Approve or reject with reason

## Models

### ExpenseCategory
- name
- description
- is_active

### Expense
- employee (FK to Employee)
- category (FK to ExpenseCategory)
- title
- description
- amount
- expense_date
- receipt (file upload)
- status (draft/submitted/approved/rejected/reimbursed)

### ReimbursementRequest
- employee (FK to Employee)
- expenses (M2M to Expense)
- total_amount
- status (pending/approved/rejected/paid)

## URLs

```
/expenses/                              # My expenses
/expenses/create/                       # Add expense
/expenses/update/<id>/                  # Edit expense
/expenses/submit/<id>/                  # Submit expense
/expenses/reimbursements/               # My reimbursements
/expenses/reimbursements/create/        # Request reimbursement
/expenses/admin/expenses/               # Approve expenses
/expenses/admin/expenses/<id>/approve/  # Approve/reject
```

## Permissions

Add these permissions for managers:
- `expenses.view_expense`
- `expenses.change_expense`
- `expenses.approve_expense`

## Quick Start

```bash
# 1. Install
cd /path/to/horilla
source horillavenv/bin/activate

# 2. Add to settings.py INSTALLED_APPS
# 3. Add to urls.py

# 4. Migrate
python manage.py makemigrations expenses
python manage.py migrate

# 5. Create categories
python manage.py shell
>>> from expenses.models import ExpenseCategory
>>> ExpenseCategory.objects.create(name='Travel')
>>> ExpenseCategory.objects.create(name='Meals')
>>> exit()

# 6. Access
# Navigate to http://localhost:8000/expenses/
```

## Customization

### Add More Fields

Edit `expenses/models.py` and add fields to Expense model:

```python
class Expense(models.Model):
    # ... existing fields ...
    project = models.CharField(max_length=100, blank=True)
    client = models.CharField(max_length=100, blank=True)
```

### Change Approval Workflow

Edit `expenses/views.py` to add multi-level approvals or notifications.

## Troubleshooting

**Issue**: Cannot see expenses module
- Ensure 'expenses' is in INSTALLED_APPS
- Run migrations
- Restart server

**Issue**: No categories available
- Create categories via admin or shell

**Issue**: Cannot upload receipts
- Check MEDIA_ROOT and MEDIA_URL in settings.py
- Ensure media directory exists and is writable

## Integration with Payroll

To integrate with payroll module, add:

```python
# In payroll module
from expenses.models import ReimbursementRequest

# Get approved reimbursements for payroll period
reimbursements = ReimbursementRequest.objects.filter(
    status='approved',
    request_date__range=[start_date, end_date]
)
```