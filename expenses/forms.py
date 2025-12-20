from django import forms
from .models import Expense, ExpenseCategory, ReimbursementRequest
from base.forms import ModelForm

class ExpenseForm(ModelForm):
    class Meta:
        model = Expense
        fields = ['category', 'title', 'description', 'amount', 'expense_date', 'receipt']
        widgets = {
            'expense_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class ExpenseCategoryForm(ModelForm):
    class Meta:
        model = ExpenseCategory
        fields = ['name', 'description']

class ReimbursementRequestForm(ModelForm):
    expenses = forms.ModelMultipleChoiceField(
        queryset=Expense.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )
    
    class Meta:
        model = ReimbursementRequest
        fields = ['expenses', 'notes']
    
    def __init__(self, *args, **kwargs):
        employee = kwargs.pop('employee', None)
        super().__init__(*args, **kwargs)
        if employee:
            self.fields['expenses'].queryset = Expense.objects.filter(
                employee=employee, 
                status='approved'
            ).exclude(
                reimbursementrequest__status__in=['pending', 'approved', 'paid']
            )