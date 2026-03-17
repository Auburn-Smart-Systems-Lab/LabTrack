"""Forms for the kits app."""

from django import forms

from apps.equipment.models import Equipment
from apps.kits.models import Kit, KitItem


class KitForm(forms.ModelForm):
    """Form for creating or editing a Kit."""

    class Meta:
        model = Kit
        fields = ['name', 'description', 'is_shared']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class KitItemForm(forms.ModelForm):
    """Form for adding a piece of equipment to a kit."""

    equipment = forms.ModelChoiceField(
        queryset=Equipment.objects.filter(is_active=True),
        empty_label='-- Select Equipment --',
    )

    class Meta:
        model = KitItem
        fields = ['equipment', 'quantity', 'notes']
        widgets = {
            'notes': forms.TextInput(),
        }

    def __init__(self, *args, kit=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Exclude equipment items that are already in this kit.
        if kit is not None:
            existing_ids = kit.items.values_list('equipment_id', flat=True)
            self.fields['equipment'].queryset = Equipment.objects.filter(
                is_active=True
            ).exclude(pk__in=existing_ids)

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is not None and quantity < 1:
            raise forms.ValidationError('Quantity must be at least 1.')
        return quantity
