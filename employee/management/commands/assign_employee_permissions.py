"""
Django Management Command for Employee Permission Assignment

This command provides a management interface for assigning permissions to employees
in the Horilla HRMS system.

Usage:
    python manage.py assign_employee_permissions --help
    python manage.py assign_employee_permissions --list-employees
    python manage.py assign_employee_permissions --list-permissions
    python manage.py assign_employee_permissions --employee 1 --permissions view_employee add_employee
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Permission
from django.db import transaction
from employee.models import Employee


class Command(BaseCommand):
    help = 'Assign permissions to employees in Horilla HRMS'

    def add_arguments(self, parser):
        parser.add_argument(
            '--list-employees',
            action='store_true',
            help='List all active employees',
        )
        parser.add_argument(
            '--list-permissions',
            action='store_true',
            help='List all available permissions',
        )
        parser.add_argument(
            '--employee',
            type=int,
            help='Employee ID to assign permissions to',
        )
        parser.add_argument(
            '--employees',
            nargs='+',
            type=int,
            help='Multiple Employee IDs for bulk operations',
        )
        parser.add_argument(
            '--permissions',
            nargs='+',
            help='Permission codenames to assign',
        )
        parser.add_argument(
            '--remove-permissions',
            nargs='+',
            help='Permission codenames to remove',
        )
        parser.add_argument(
            '--show-permissions',
            action='store_true',
            help='Show current permissions for employee',
        )
        parser.add_argument(
            '--replace',
            action='store_true',
            help='Replace existing permissions instead of adding',
        )

    def handle(self, *args, **options):
        if options['list_employees']:
            self.list_employees()
        elif options['list_permissions']:
            self.list_permissions()
        elif options['show_permissions'] and options['employee']:
            self.show_employee_permissions(options['employee'])
        elif options['employee'] and options['permissions']:
            self.assign_permissions(
                options['employee'], 
                options['permissions'], 
                options['replace']
            )
        elif options['employee'] and options['remove_permissions']:
            self.remove_permissions(options['employee'], options['remove_permissions'])
        elif options['employees'] and options['permissions']:
            self.bulk_assign_permissions(
                options['employees'], 
                options['permissions'], 
                options['replace']
            )
        else:
            self.print_help('manage.py', 'assign_employee_permissions')

    def list_employees(self):
        """List all active employees."""
        employees = Employee.objects.filter(is_active=True).select_related('employee_user_id')
        
        self.stdout.write(self.style.SUCCESS('\n=== ACTIVE EMPLOYEES ==='))
        self.stdout.write(f"{'ID':<5} {'Badge ID':<10} {'Name':<30} {'Email':<30}")
        self.stdout.write("-" * 80)
        
        for emp in employees:
            name = f"{emp.employee_first_name} {emp.employee_last_name}"
            email = emp.email or "N/A"
            badge_id = emp.badge_id or "N/A"
            self.stdout.write(f"{emp.id:<5} {badge_id:<10} {name:<30} {email:<30}")

    def list_permissions(self):
        """List all available permissions grouped by app."""
        permissions = Permission.objects.all().select_related('content_type')
        permissions_by_app = {}
        
        for perm in permissions:
            app_label = perm.content_type.app_label
            if app_label not in permissions_by_app:
                permissions_by_app[app_label] = []
            permissions_by_app[app_label].append(perm)
        
        self.stdout.write(self.style.SUCCESS('\n=== AVAILABLE PERMISSIONS ==='))
        for app_label, perms in sorted(permissions_by_app.items()):
            self.stdout.write(f"\n{app_label.upper()}:")
            for perm in perms:
                self.stdout.write(f"  {perm.codename:<40} - {perm.name}")

    def show_employee_permissions(self, employee_id):
        """Show current permissions for an employee."""
        try:
            employee = Employee.objects.get(id=employee_id, is_active=True)
            user = employee.employee_user_id
            
            if not user:
                raise CommandError(f"Employee {employee_id} has no associated user account.")
            
            user_permissions = user.user_permissions.all()
            group_permissions = Permission.objects.filter(group__user=user)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n=== PERMISSIONS FOR {employee.employee_first_name} {employee.employee_last_name} ==='
                )
            )
            
            if user_permissions:
                self.stdout.write("\nDirect Permissions:")
                for perm in user_permissions:
                    self.stdout.write(f"  ✓ {perm.codename} - {perm.name}")
            
            if group_permissions:
                self.stdout.write("\nGroup Permissions:")
                for perm in group_permissions:
                    groups = user.groups.filter(permissions=perm)
                    group_names = ", ".join([g.name for g in groups])
                    self.stdout.write(f"  ✓ {perm.codename} - {perm.name} (via {group_names})")
            
            if not user_permissions and not group_permissions:
                self.stdout.write("  No permissions assigned.")
                
        except Employee.DoesNotExist:
            raise CommandError(f"Employee with ID {employee_id} not found or inactive.")

    @transaction.atomic
    def assign_permissions(self, employee_id, permission_codenames, replace=False):
        """Assign permissions to an employee."""
        try:
            employee = Employee.objects.get(id=employee_id, is_active=True)
            user = employee.employee_user_id
            
            if not user:
                raise CommandError(f"Employee {employee_id} has no associated user account.")
            
            # Get permission objects
            permissions = Permission.objects.filter(codename__in=permission_codenames)
            found_codenames = set(permissions.values_list('codename', flat=True))
            missing_codenames = set(permission_codenames) - found_codenames
            
            if missing_codenames:
                self.stdout.write(
                    self.style.WARNING(
                        f"Warning: The following permissions were not found: {', '.join(missing_codenames)}"
                    )
                )
            
            if not permissions:
                raise CommandError("No valid permissions found.")
            
            # Assign permissions
            if replace:
                user.user_permissions.clear()
                user.user_permissions.set(permissions)
                action = "replaced with"
            else:
                user.user_permissions.add(*permissions)
                action = "added"
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nSuccess: {len(permissions)} permissions {action} for {employee.employee_first_name} {employee.employee_last_name}'
                )
            )
            
            # Show assigned permissions
            for perm in permissions:
                self.stdout.write(f"  ✓ {perm.codename} - {perm.name}")
                
        except Employee.DoesNotExist:
            raise CommandError(f"Employee with ID {employee_id} not found or inactive.")

    @transaction.atomic
    def remove_permissions(self, employee_id, permission_codenames):
        """Remove specific permissions from an employee."""
        try:
            employee = Employee.objects.get(id=employee_id, is_active=True)
            user = employee.employee_user_id
            
            if not user:
                raise CommandError(f"Employee {employee_id} has no associated user account.")
            
            permissions = Permission.objects.filter(codename__in=permission_codenames)
            
            if not permissions:
                raise CommandError("No valid permissions found to remove.")
            
            user.user_permissions.remove(*permissions)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nSuccess: {len(permissions)} permissions removed from {employee.employee_first_name} {employee.employee_last_name}'
                )
            )
            
            for perm in permissions:
                self.stdout.write(f"  ✗ {perm.codename} - {perm.name}")
                
        except Employee.DoesNotExist:
            raise CommandError(f"Employee with ID {employee_id} not found or inactive.")

    def bulk_assign_permissions(self, employee_ids, permission_codenames, replace=False):
        """Assign permissions to multiple employees."""
        success_count = 0
        
        self.stdout.write(self.style.SUCCESS('\n=== BULK PERMISSION ASSIGNMENT ==='))
        self.stdout.write(f"Employees: {len(employee_ids)}")
        self.stdout.write(f"Permissions: {len(permission_codenames)}")
        self.stdout.write(f"Mode: {'Replace' if replace else 'Add'}")
        self.stdout.write("-" * 50)
        
        for emp_id in employee_ids:
            try:
                self.assign_permissions(emp_id, permission_codenames, replace)
                success_count += 1
            except CommandError as e:
                self.stdout.write(self.style.ERROR(f"Failed for employee {emp_id}: {e}"))
        
        self.stdout.write(self.style.SUCCESS(f'\n=== SUMMARY ==='))
        self.stdout.write(f"Successfully processed: {success_count}/{len(employee_ids)} employees")