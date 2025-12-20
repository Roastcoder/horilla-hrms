"""
sales_incentive/sidebar.py

To set Horilla sidebar for sales incentive
"""

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as trans

MENU = trans("Sales Incentive")
IMG_SRC = "images/ui/wallet-outline.svg"

SUBMENUS = [
    {
        "menu": trans("Dashboard"),
        "redirect": reverse_lazy("sales_incentive:dashboard"),
    },
    {
        "menu": trans("Incentive Slabs"),
        "redirect": reverse_lazy("sales_incentive:incentive-slab-view"),
    },
    {
        "menu": trans("Loan Types"),
        "redirect": reverse_lazy("sales_incentive:loan-type-view"),
    },
    {
        "menu": trans("Leads"),
        "redirect": reverse_lazy("sales_incentive:lead-view"),
    },
    {
        "menu": trans("Manual Attendance"),
        "redirect": reverse_lazy("sales_incentive:manual-attendance"),
    },
]