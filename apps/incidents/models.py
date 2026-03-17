from django.db import models


class IncidentReport(models.Model):
    """Records a damage, safety, or operational incident involving equipment."""

    SEVERITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('INVESTIGATING', 'Investigating'),
        ('RESOLVED', 'Resolved'),
        ('CLOSED', 'Closed'),
    ]

    equipment = models.ForeignKey(
        'equipment.Equipment',
        on_delete=models.CASCADE,
        related_name='incidents',
    )
    reported_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reported_incidents',
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='MEDIUM')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    image = models.ImageField(upload_to='incidents/', blank=True, null=True)
    resolution = models.TextField(blank=True)
    resolved_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_incidents',
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.equipment.name})"

    class Meta:
        ordering = ['-created_at']


class MaintenanceLog(models.Model):
    """Records a scheduled or completed maintenance activity for equipment."""

    MAINTENANCE_TYPE_CHOICES = [
        ('PREVENTIVE', 'Preventive'),
        ('CORRECTIVE', 'Corrective'),
        ('INSPECTION', 'Inspection'),
        ('CALIBRATION', 'Calibration'),
    ]
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    equipment = models.ForeignKey(
        'equipment.Equipment',
        on_delete=models.CASCADE,
        related_name='maintenance_logs',
    )
    maintenance_type = models.CharField(
        max_length=20, choices=MAINTENANCE_TYPE_CHOICES
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    performed_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='maintenance_performed',
    )
    description = models.TextField()
    scheduled_date = models.DateField()
    completed_date = models.DateField(null=True, blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.equipment.name} - {self.maintenance_type} ({self.status})"

    class Meta:
        ordering = ['-scheduled_date']


class CalibrationLog(models.Model):
    """Records a calibration check for precision equipment."""

    STATUS_CHOICES = [
        ('PASS', 'Pass'),
        ('FAIL', 'Fail'),
        ('PENDING', 'Pending'),
    ]

    equipment = models.ForeignKey(
        'equipment.Equipment',
        on_delete=models.CASCADE,
        related_name='calibration_logs',
    )
    calibrated_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='calibrations_performed',
    )
    calibration_date = models.DateField()
    next_calibration_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    certificate_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.equipment.name} calibrated on {self.calibration_date}"

    class Meta:
        ordering = ['-calibration_date']
