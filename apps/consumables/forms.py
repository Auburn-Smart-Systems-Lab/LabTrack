"""Forms for the consumables app."""

from django import forms

from apps.consumables.models import Consumable, ConsumableUsageLog
from apps.equipment.models import Category, Location
from apps.projects.models import Project


class ConsumableForm(forms.ModelForm):
    """Create or update a Consumable record."""

    class Meta:
        model = Consumable
        fields = [
            'name',
            'description',
            'category',
            'location',
            'quantity',
            'unit',
            'low_stock_threshold',
            'unit_cost',
            'supplier',
            'notes',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Consumable name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unit': forms.Select(attrs={'class': 'form-select'}),
            'low_stock_threshold': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unit_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'supplier': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ConsumableUsageLogForm(forms.ModelForm):
    """Log usage of a consumable item."""

    project = forms.ModelChoiceField(
        queryset=Project.objects.filter(status='ACTIVE'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='-- No project --',
    )

    class Meta:
        model = ConsumableUsageLog
        fields = ['quantity_used', 'project', 'purpose']
        widgets = {
            'quantity_used': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}
            ),
            'purpose': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Describe the purpose of usage'}
            ),
        }

    def __init__(self, *args, consumable=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.consumable = consumable

    def clean_quantity_used(self):
        qty = self.cleaned_data.get('quantity_used')
        if qty is not None and qty <= 0:
            raise forms.ValidationError('Quantity used must be greater than zero.')
        if self.consumable and qty is not None and qty > self.consumable.quantity:
            raise forms.ValidationError(
                f'Not enough stock. Available: {self.consumable.quantity} {self.consumable.unit}.'
            )
        return qty


class RestockForm(forms.Form):
    """Add stock to an existing consumable."""

    quantity_to_add = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0.01,
        widget=forms.NumberInput(
            attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Quantity to add'}
        ),
        label='Quantity to Add',
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional notes'}),
        label='Notes',
    )
