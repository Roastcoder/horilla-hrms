"""
Management command to initialize default incentive slabs and loan types
"""

from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _
from decimal import Decimal

from sales_incentive_models import IncentiveSlab, LoanType, CallAttendanceConfig


class Command(BaseCommand):
    help = 'Initialize default incentive slabs, loan types, and configurations'

    def handle(self, *args, **options):
        self.stdout.write('Initializing sales incentive system...')
        
        # Create default incentive slabs
        slabs_data = [
            (1, 5, 300),
            (6, 10, 400),
            (11, 15, 500),
            (16, 20, 600),
            (21, 25, 700),
            (26, 30, 750),
            (31, 35, 800),
            (36, 40, 850),
            (41, 45, 900),
            (46, 50, 950),
            (51, None, 1000),  # 51+ Lac
        ]
        
        for min_amt, max_amt, incentive in slabs_data:
            slab, created = IncentiveSlab.objects.get_or_create(
                min_amount=Decimal(str(min_amt)),
                max_amount=Decimal(str(max_amt)) if max_amt else None,
                defaults={'incentive_per_lac': Decimal(str(incentive))}
            )
            if created:
                self.stdout.write(f'Created slab: {slab}')
        
        # Create default loan types
        loan_types_data = [
            ('Home Loan', 0.2),
            ('Loan Against Property', 0.3),
            ('Commercial Vehicle Loan', 0.2),
            ('Personal Loan', 1.0),
            ('Business Loan', 1.0),
            ('Used Car Loan', 1.0),
            ('New Car Loan', 0.2),
        ]
        
        for name, points in loan_types_data:
            loan_type, created = LoanType.objects.get_or_create(
                name=name,
                defaults={'points_per_lac': Decimal(str(points))}
            )
            if created:
                self.stdout.write(f'Created loan type: {loan_type}')
        
        # Create default call attendance config
        config, created = CallAttendanceConfig.objects.get_or_create(
            is_active=True,
            defaults={
                'daily_required_minutes': 400,
                'present_threshold': 171,
                'half_day_threshold': 121,
                'absent_threshold': 120,
            }
        )
        if created:
            self.stdout.write(f'Created call attendance config: {config}')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully initialized sales incentive system')
        )