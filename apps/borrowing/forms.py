"""Forms for the borrowing app."""

from django import forms
from django.utils import timezone

from apps.borrowing.models import BorrowRequest
from apps.equipment.models import Equipment
from apps.kits.models import Kit
from apps.projects.models import Project


class BorrowRequestForm(forms.ModelForm):
    """Form for creating a borrow request for a piece of equipment or a kit."""

    equipment = forms.ModelChoiceField(
        queryset=Equipment.objects.filter(is_active=True),
        required=False,
        empty_label='-- Select Equipment --',
        help_text='Select equipment OR a kit, not both.',
    )
    kit = forms.ModelChoiceField(
        queryset=Kit.objects.filter(is_active=True),
        required=False,
        empty_label='-- Select Kit --',
        help_text='Select a kit OR equipment, not both.',
    )
    project = forms.ModelChoiceField(
        queryset=Project.objects.filter(status='ACTIVE'),
        required=False,
        empty_label='-- No Project --',
    )

    class Meta:
        model = BorrowRequest
        fields = ['equipment', 'kit', 'project', 'purpose', 'due_date']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'purpose': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        equipment = cleaned_data.get('equipment')
        kit = cleaned_data.get('kit')
        due_date = cleaned_data.get('due_date')

        # Exactly one of equipment or kit must be selected.
        if not equipment and not kit:
            raise forms.ValidationError(
                'You must select either a piece of equipment or a kit.'
            )
        if equipment and kit:
            raise forms.ValidationError(
                'Please select either equipment or a kit, not both.'
            )

        # Validate equipment availability.
        if equipment and equipment.status != 'AVAILABLE':
            raise forms.ValidationError(
                f'"{equipment.name}" is currently not available '
                f'(status: {equipment.get_status_display()}).'
            )

        # Validate kit availability: all items in the kit must be available.
        if kit:
            unavailable = [
                item.equipment.name
                for item in kit.items.select_related('equipment')
                if item.equipment.status != 'AVAILABLE'
            ]
            if unavailable:
                raise forms.ValidationError(
                    f'The following items in kit "{kit.name}" are not available: '
                    + ', '.join(unavailable)
                )

        # Due date must be in the future.
        if due_date and due_date < timezone.now().date():
            raise forms.ValidationError('Due date must be today or a future date.')

        return cleaned_data


class ReturnForm(forms.Form):
    """Form for recording the return of borrowed equipment or a kit."""

    CONDITION_CHOICES = [
        ('EXCELLENT', 'Excellent'),
        ('GOOD', 'Good'),
        ('FAIR', 'Fair'),
        ('POOR', 'Poor'),
        ('DAMAGED', 'Damaged'),
    ]

    return_condition = forms.ChoiceField(
        choices=CONDITION_CHOICES,
        initial='GOOD',
        help_text='Condition of the item on return.',
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        help_text='Any notes about the return (damage, issues, etc.).',
    )
