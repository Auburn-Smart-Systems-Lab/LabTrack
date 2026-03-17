"""Forms for the incidents app."""

from django import forms

from apps.incidents.models import CalibrationLog, IncidentReport, MaintenanceLog


class IncidentReportForm(forms.ModelForm):
    """Report a new incident involving a piece of equipment."""

    class Meta:
        model = IncidentReport
        fields = ['equipment', 'title', 'description', 'severity', 'image']
        widgets = {
            'equipment': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Brief summary of the incident'}
            ),
            'description': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Detailed description'}
            ),
            'severity': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class IncidentUpdateForm(forms.ModelForm):
    """Admin form to update the status or resolve an incident."""

    class Meta:
        model = IncidentReport
        fields = ['status', 'resolution']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'resolution': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                    'placeholder': 'Describe the resolution or findings',
                }
            ),
        }


class MaintenanceLogForm(forms.ModelForm):
    """Schedule or record a maintenance activity."""

    class Meta:
        model = MaintenanceLog
        fields = [
            'equipment',
            'maintenance_type',
            'description',
            'scheduled_date',
            'cost',
            'notes',
        ]
        widgets = {
            'equipment': forms.Select(attrs={'class': 'form-select'}),
            'maintenance_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'scheduled_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class MaintenanceCompleteForm(forms.ModelForm):
    """Admin form to mark a maintenance log as completed."""

    class Meta:
        model = MaintenanceLog
        fields = ['completed_date', 'notes', 'status']
        widgets = {
            'completed_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Completion notes'}
            ),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_status(self):
        status = self.cleaned_data.get('status')
        if status not in ('COMPLETED', 'CANCELLED'):
            raise forms.ValidationError('Status must be Completed or Cancelled when submitting this form.')
        return status


class CalibrationLogForm(forms.ModelForm):
    """Record a calibration event for precision equipment."""

    class Meta:
        model = CalibrationLog
        fields = [
            'equipment',
            'calibration_date',
            'next_calibration_date',
            'status',
            'certificate_number',
            'notes',
        ]
        widgets = {
            'equipment': forms.Select(attrs={'class': 'form-select'}),
            'calibration_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'next_calibration_date': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'}
            ),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'certificate_number': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
