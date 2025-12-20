# Employee Permission Assignment System for Horilla HRMS

This system provides a comprehensive solution for managing employee permissions in Horilla HRMS. It includes both command-line tools and a web interface for assigning, viewing, and managing permissions efficiently.

## 🚀 Features

- **Command-line Interface**: Manage permissions via Django management commands
- **Web Interface**: User-friendly web interface for permission assignment
- **Bulk Operations**: Assign permissions to multiple employees at once
- **Permission Viewing**: View current permissions for any employee
- **Integration**: Seamlessly integrates with existing Horilla permission system
- **Safety**: Transaction-based operations ensure data consistency

## 📁 Files Overview

```
employee-permission-assign/
├── employee_permission_assign.py          # Standalone Python script
├── employee/management/commands/
│   └── assign_employee_permissions.py     # Django management command
├── employee/templates/employee/
│   └── permission_assignment.html         # Web interface template
├── employee_permission_views.py           # Django views for web interface
├── employee_permission_urls.py            # URL patterns
└── README.md                              # This file
```

## 🛠️ Installation & Setup

### 1. Copy Files to Horilla Directory

Copy all files to your Horilla installation directory:

```bash
# Copy the standalone script
cp employee_permission_assign.py /path/to/horilla/

# Copy the management command
cp employee/management/commands/assign_employee_permissions.py /path/to/horilla/employee/management/commands/

# Copy the template
cp employee/templates/employee/permission_assignment.html /path/to/horilla/employee/templates/employee/

# Copy the views
cp employee_permission_views.py /path/to/horilla/

# Copy the URL patterns
cp employee_permission_urls.py /path/to/horilla/
```

### 2. Create Management Command Directory (if needed)

```bash
cd /path/to/horilla/employee/
mkdir -p management/commands
touch management/__init__.py
touch management/commands/__init__.py
```

### 3. Integrate URLs

Add the following to your main `urls.py` file (usually `horilla/urls.py`):

```python
# Add these imports at the top
from employee_permission_views import (
    employee_permission_assignment_view,
    get_employee_permissions,
    assign_employee_permissions,
    remove_employee_permissions,
    bulk_assign_employee_permissions
)

# Add these URL patterns to your urlpatterns list
urlpatterns = [
    # ... existing patterns ...
    
    # Employee Permission Assignment
    path('employee-permission-assignment/', employee_permission_assignment_view, name='employee-permission-assignment'),
    path('employee-permissions/<int:employee_id>/', get_employee_permissions, name='get-employee-permissions'),
    path('assign-employee-permissions/', assign_employee_permissions, name='assign-employee-permissions'),
    path('remove-employee-permissions/', remove_employee_permissions, name='remove-employee-permissions'),
    path('bulk-assign-employee-permissions/', bulk_assign_employee_permissions, name='bulk-assign-employee-permissions'),
    
    # ... rest of your patterns ...
]
```

### 4. Add Navigation Link (Optional)

Add a link to the permission assignment interface in your navigation template:

```html
<a href="{% url 'employee-permission-assignment' %}" class="nav-link">
    <i class="fas fa-user-shield"></i> Employee Permissions
</a>
```

## 📋 Usage

### Command Line Interface

#### 1. Standalone Python Script

```bash
# Navigate to Horilla directory
cd /path/to/horilla/

# Activate virtual environment
source horillavenv/bin/activate

# List all employees
python employee_permission_assign.py --list-employees

# List all permissions
python employee_permission_assign.py --list-permissions

# Show permissions for employee ID 1
python employee_permission_assign.py --employee 1 --show-permissions

# Assign permissions to employee
python employee_permission_assign.py --employee 1 --permissions view_employee add_employee

# Replace all permissions for employee
python employee_permission_assign.py --employee 1 --permissions view_employee --replace

# Remove permissions from employee
python employee_permission_assign.py --employee 1 --remove-permissions view_employee

# Bulk assign permissions to multiple employees
python employee_permission_assign.py --employees 1 2 3 --permissions view_employee add_employee
```

#### 2. Django Management Command

```bash
# Navigate to Horilla directory
cd /path/to/horilla/

# Activate virtual environment
source horillavenv/bin/activate

# List all employees
python manage.py assign_employee_permissions --list-employees

# List all permissions
python manage.py assign_employee_permissions --list-permissions

# Show permissions for employee ID 1
python manage.py assign_employee_permissions --employee 1 --show-permissions

# Assign permissions to employee
python manage.py assign_employee_permissions --employee 1 --permissions view_employee add_employee

# Replace all permissions for employee
python manage.py assign_employee_permissions --employee 1 --permissions view_employee --replace

# Remove permissions from employee
python manage.py assign_employee_permissions --employee 1 --remove-permissions view_employee

# Bulk assign permissions to multiple employees
python manage.py assign_employee_permissions --employees 1 2 3 --permissions view_employee add_employee
```

### Web Interface

1. **Access the Interface**: Navigate to `/employee-permission-assignment/` in your browser
2. **Select Employee**: Choose an employee from the dropdown
3. **View Current Permissions**: Current permissions are automatically loaded
4. **Select Permissions**: Browse and select permissions by app category
5. **Choose Mode**: 
   - **Add**: Add to existing permissions
   - **Replace**: Replace all existing permissions
6. **Assign**: Click "Assign Permissions" to apply changes

### Common Permission Codenames

Here are some commonly used permission codenames in Horilla:

#### Employee Permissions
- `view_employee` - View employee records
- `add_employee` - Add new employees
- `change_employee` - Edit employee information
- `delete_employee` - Delete employees

#### Attendance Permissions
- `view_attendance` - View attendance records
- `add_attendance` - Add attendance entries
- `change_attendance` - Edit attendance records

#### Leave Permissions
- `view_leaverequest` - View leave requests
- `add_leaverequest` - Create leave requests
- `change_leaverequest` - Edit leave requests
- `approve_leaverequest` - Approve leave requests

#### Payroll Permissions
- `view_payslip` - View payslips
- `add_payslip` - Create payslips
- `change_payslip` - Edit payslips

## 🔒 Security & Permissions

### Required Permissions

To use the permission assignment system, users need:

- `auth.change_permission` - To assign/remove permissions
- `auth.view_permission` - To view permissions
- `employee.view_employee` - To view employee list

### Best Practices

1. **Principle of Least Privilege**: Only assign necessary permissions
2. **Regular Audits**: Regularly review employee permissions
3. **Group-based Permissions**: Use groups for common permission sets
4. **Documentation**: Document permission assignments and changes

## 🐛 Troubleshooting

### Common Issues

1. **"Employee has no associated user account"**
   - Ensure the employee has a linked user account
   - Check that `employee.employee_user_id` is not null

2. **"Permission not found"**
   - Verify permission codenames are correct
   - Use `--list-permissions` to see available permissions

3. **"Access denied"**
   - Ensure you have the required permissions
   - Check that you're logged in as a user with appropriate rights

4. **Template not found**
   - Ensure the template is in the correct directory
   - Check that the path matches your template structure

### Debug Mode

For debugging, you can enable Django's debug mode and check the logs:

```python
# In settings.py
DEBUG = True
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## 📊 Examples

### Example 1: HR Manager Setup

```bash
# Assign comprehensive HR permissions to employee ID 5
python manage.py assign_employee_permissions --employee 5 --permissions \
    view_employee add_employee change_employee \
    view_leaverequest change_leaverequest approve_leaverequest \
    view_attendance change_attendance
```

### Example 2: Department Manager Setup

```bash
# Assign limited management permissions to employee ID 10
python manage.py assign_employee_permissions --employee 10 --permissions \
    view_employee view_leaverequest approve_leaverequest view_attendance
```

### Example 3: Bulk Setup for New Team

```bash
# Assign basic permissions to multiple new employees
python manage.py assign_employee_permissions --employees 15 16 17 18 --permissions \
    view_employee view_leaverequest add_leaverequest view_attendance
```

## 🔄 Integration with Existing System

This system integrates seamlessly with Horilla's existing permission framework:

- **Uses Django's built-in Permission model**
- **Respects existing group permissions**
- **Works with Horilla's permission decorators**
- **Maintains audit trails through Django's admin**

## 📈 Performance Considerations

- **Database Queries**: Uses `select_related()` for efficient queries
- **Transactions**: All operations are wrapped in database transactions
- **Caching**: Consider implementing caching for frequently accessed permissions
- **Bulk Operations**: Use bulk operations for multiple employees

## 🤝 Contributing

To extend this system:

1. **Add new views** in `employee_permission_views.py`
2. **Create new templates** following Horilla's template structure
3. **Add URL patterns** in the appropriate URL configuration
4. **Test thoroughly** with different permission combinations

## 📝 License

This employee permission assignment system follows the same license as Horilla HRMS (LGPL-3.0).

---

**Need Help?** 

- Check the Horilla documentation
- Review Django's permission system documentation
- Test with a small set of employees first
- Use the `--show-permissions` flag to verify assignments