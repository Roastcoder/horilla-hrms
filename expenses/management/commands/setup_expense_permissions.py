"""
Django management command to set up roles and permissions for expenses module
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from expenses.models import Expense, ExpenseCategory, ReimbursementRequest

class Command(BaseCommand):
    help = 'Set up roles and permissions for expenses module'

    def handle(self, *args, **options):
        # Create permissions
        expense_ct = ContentType.objects.get_for_model(Expense)
        category_ct = ContentType.objects.get_for_model(ExpenseCategory)
        reimbursement_ct = ContentType.objects.get_for_model(ReimbursementRequest)

        # Custom permissions
        permissions_to_create = [
            ('approve_expense', 'Can approve expenses', expense_ct),
            ('manage_expense_categories', 'Can manage expense categories', category_ct),
            ('approve_reimbursement', 'Can approve reimbursement requests', reimbursement_ct),
        ]

        for codename, name, content_type in permissions_to_create:
            permission, created = Permission.objects.get_or_create(
                codename=codename,
                name=name,
                content_type=content_type,
            )
            if created:
                self.stdout.write(f'Created permission: {name}')

        # Create groups and assign permissions
        groups_config = {
            'Expense Managers': [
                'view_expense', 'add_expense', 'change_expense', 'delete_expense',
                'approve_expense',
                'view_expensecategory', 'add_expensecategory', 'change_expensecategory',
                'manage_expense_categories',
                'view_reimbursementrequest', 'change_reimbursementrequest',
                'approve_reimbursement',
            ],
            'Expense Approvers': [
                'view_expense', 'change_expense', 'approve_expense',
                'view_reimbursementrequest', 'approve_reimbursement',
            ],
            'Employees': [
                'add_expense', 'view_expense', 'change_expense',
                'add_reimbursementrequest', 'view_reimbursementrequest',
            ],
        }

        for group_name, permission_codenames in groups_config.items():
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(f'Created group: {group_name}')

            # Add permissions to group
            for codename in permission_codenames:
                try:
                    permission = Permission.objects.get(codename=codename)
                    group.permissions.add(permission)
                    self.stdout.write(f'Added {codename} to {group_name}')
                except Permission.DoesNotExist:
                    self.stdout.write(f'Permission {codename} not found')

        self.stdout.write(self.style.SUCCESS('Successfully set up expenses roles and permissions!'))