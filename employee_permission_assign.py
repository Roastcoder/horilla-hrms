#!/usr/bin/env python3
"""
Employee Permission Assignment System for Horilla HRMS

This script provides a simple interface to assign permissions to employees
in the Horilla HRMS system. It integrates with the existing permission
structure and provides a streamlined way to manage employee permissions.

Usage:
    python employee_permission_assign.py --employee <employee_id> --permissions <permission_codenames>
    python employee_permission_assign.py --list-employees
    python employee_permission_assign.py --list-permissions
"""

import os
import sys
import django
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
django.setup()

from employee.models import Employee


class EmployeePermissionAssigner:
    """
    A class to handle employee permission assignments in Horilla HRMS.
    """
    
    def __init__(self):
        self.available_permissions = self._get_available_permissions()
    
    def _get_available_permissions(self):
        """Get all available permissions in the system."""
        return Permission.objects.all().select_related('content_type')
    
    def list_employees(self):
        """List all active employees."""
        employees = Employee.objects.filter(is_active=True).select_related('employee_user_id')
        
        print("\n=== ACTIVE EMPLOYEES ===")
        print(f"{'ID':<5} {'Badge ID':<10} {'Name':<30} {'Email':<30}")
        print("-" * 80)
        
        for emp in employees:
            name = f"{emp.employee_first_name} {emp.employee_last_name}"
            email = emp.email or "N/A"
            badge_id = emp.badge_id or "N/A"
            print(f"{emp.id:<5} {badge_id:<10} {name:<30} {email:<30}")
        
        return employees
    
    def list_permissions(self):
        """List all available permissions grouped by app."""
        permissions_by_app = {}
        
        for perm in self.available_permissions:
            app_label = perm.content_type.app_label
            if app_label not in permissions_by_app:
                permissions_by_app[app_label] = []
            permissions_by_app[app_label].append(perm)
        
        print("\n=== AVAILABLE PERMISSIONS ===")
        for app_label, perms in sorted(permissions_by_app.items()):
            print(f"\n{app_label.upper()}:")
            for perm in perms:
                print(f"  {perm.codename:<40} - {perm.name}")
        
        return permissions_by_app
    
    def get_employee_permissions(self, employee_id):
        """Get current permissions for an employee."""
        try:
            employee = Employee.objects.get(id=employee_id, is_active=True)
            user = employee.employee_user_id
            
            if not user:
                print(f"Error: Employee {employee_id} has no associated user account.")
                return None
            
            user_permissions = user.user_permissions.all()
            group_permissions = Permission.objects.filter(group__user=user)
            
            all_permissions = set(user_permissions) | set(group_permissions)
            
            print(f"\n=== PERMISSIONS FOR {employee.employee_first_name} {employee.employee_last_name} ===")
            
            if user_permissions:
                print("\nDirect Permissions:")
                for perm in user_permissions:
                    print(f"  {perm.codename} - {perm.name}")
            
            if group_permissions:
                print("\nGroup Permissions:")
                for perm in group_permissions:
                    groups = user.groups.filter(permissions=perm)
                    group_names = ", ".join([g.name for g in groups])
                    print(f"  {perm.codename} - {perm.name} (via {group_names})")
            
            if not all_permissions:
                print("  No permissions assigned.")
            
            return all_permissions
            
        except Employee.DoesNotExist:
            print(f"Error: Employee with ID {employee_id} not found or inactive.")
            return None
    
    @transaction.atomic
    def assign_permissions(self, employee_id, permission_codenames, replace=False):
        """
        Assign permissions to an employee.
        
        Args:
            employee_id (int): Employee ID
            permission_codenames (list): List of permission codenames
            replace (bool): If True, replace existing permissions. If False, add to existing.
        """
        try:
            employee = Employee.objects.get(id=employee_id, is_active=True)
            user = employee.employee_user_id
            
            if not user:
                print(f"Error: Employee {employee_id} has no associated user account.")
                return False
            
            # Get permission objects
            permissions = Permission.objects.filter(codename__in=permission_codenames)
            found_codenames = set(permissions.values_list('codename', flat=True))
            missing_codenames = set(permission_codenames) - found_codenames
            
            if missing_codenames:
                print(f"Warning: The following permissions were not found: {', '.join(missing_codenames)}")
            
            if not permissions:
                print("Error: No valid permissions found.")
                return False
            
            # Assign permissions
            if replace:
                user.user_permissions.clear()
                user.user_permissions.set(permissions)
                action = "replaced with"
            else:
                user.user_permissions.add(*permissions)
                action = "added"
            
            print(f"\nSuccess: {len(permissions)} permissions {action} for {employee.employee_first_name} {employee.employee_last_name}")
            
            # Show assigned permissions
            for perm in permissions:
                print(f"  ✓ {perm.codename} - {perm.name}")
            
            return True
            
        except Employee.DoesNotExist:
            print(f"Error: Employee with ID {employee_id} not found or inactive.")
            return False
        except Exception as e:
            print(f"Error: {str(e)}")
            return False
    
    @transaction.atomic
    def remove_permissions(self, employee_id, permission_codenames):
        """Remove specific permissions from an employee."""
        try:
            employee = Employee.objects.get(id=employee_id, is_active=True)
            user = employee.employee_user_id
            
            if not user:
                print(f"Error: Employee {employee_id} has no associated user account.")
                return False
            
            permissions = Permission.objects.filter(codename__in=permission_codenames)
            
            if not permissions:
                print("Error: No valid permissions found to remove.")
                return False
            
            user.user_permissions.remove(*permissions)
            
            print(f"\nSuccess: {len(permissions)} permissions removed from {employee.employee_first_name} {employee.employee_last_name}")
            
            for perm in permissions:
                print(f"  ✗ {perm.codename} - {perm.name}")
            
            return True
            
        except Employee.DoesNotExist:
            print(f"Error: Employee with ID {employee_id} not found or inactive.")
            return False
        except Exception as e:
            print(f"Error: {str(e)}")
            return False
    
    def bulk_assign_permissions(self, employee_ids, permission_codenames, replace=False):
        """Assign permissions to multiple employees."""
        success_count = 0
        
        print(f"\n=== BULK PERMISSION ASSIGNMENT ===")
        print(f"Employees: {len(employee_ids)}")
        print(f"Permissions: {len(permission_codenames)}")
        print(f"Mode: {'Replace' if replace else 'Add'}")
        print("-" * 50)
        
        for emp_id in employee_ids:
            if self.assign_permissions(emp_id, permission_codenames, replace):
                success_count += 1
        
        print(f"\n=== SUMMARY ===")
        print(f"Successfully processed: {success_count}/{len(employee_ids)} employees")
        
        return success_count


def main():
    """Main function to handle command line interface."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Employee Permission Assignment for Horilla HRMS')
    parser.add_argument('--list-employees', action='store_true', help='List all active employees')
    parser.add_argument('--list-permissions', action='store_true', help='List all available permissions')
    parser.add_argument('--employee', type=int, help='Employee ID')
    parser.add_argument('--employees', nargs='+', type=int, help='Multiple Employee IDs for bulk operations')
    parser.add_argument('--permissions', nargs='+', help='Permission codenames to assign')
    parser.add_argument('--remove-permissions', nargs='+', help='Permission codenames to remove')
    parser.add_argument('--show-permissions', action='store_true', help='Show current permissions for employee')
    parser.add_argument('--replace', action='store_true', help='Replace existing permissions instead of adding')
    
    args = parser.parse_args()
    
    assigner = EmployeePermissionAssigner()
    
    if args.list_employees:
        assigner.list_employees()
    
    elif args.list_permissions:
        assigner.list_permissions()
    
    elif args.show_permissions and args.employee:
        assigner.get_employee_permissions(args.employee)
    
    elif args.employee and args.permissions:
        assigner.assign_permissions(args.employee, args.permissions, args.replace)
    
    elif args.employee and args.remove_permissions:
        assigner.remove_permissions(args.employee, args.remove_permissions)
    
    elif args.employees and args.permissions:
        assigner.bulk_assign_permissions(args.employees, args.permissions, args.replace)
    
    else:
        parser.print_help()
        print("\nExamples:")
        print("  # List all employees")
        print("  python employee_permission_assign.py --list-employees")
        print()
        print("  # List all permissions")
        print("  python employee_permission_assign.py --list-permissions")
        print()
        print("  # Show permissions for employee ID 1")
        print("  python employee_permission_assign.py --employee 1 --show-permissions")
        print()
        print("  # Assign permissions to employee")
        print("  python employee_permission_assign.py --employee 1 --permissions view_employee add_employee")
        print()
        print("  # Replace all permissions for employee")
        print("  python employee_permission_assign.py --employee 1 --permissions view_employee --replace")
        print()
        print("  # Remove permissions from employee")
        print("  python employee_permission_assign.py --employee 1 --remove-permissions view_employee")
        print()
        print("  # Bulk assign permissions to multiple employees")
        print("  python employee_permission_assign.py --employees 1 2 3 --permissions view_employee add_employee")


if __name__ == '__main__':
    main()