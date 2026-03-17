from django.db import models


class ActivityLog(models.Model):
    """
    A system-wide audit log entry recording actions performed by users.
    Uses simple label + id fields instead of GenericForeignKey for simplicity.
    """

    ACTION_CHOICES = [
        # Equipment
        ('EQUIPMENT_CREATED', 'Equipment Created'),
        ('EQUIPMENT_UPDATED', 'Equipment Updated'),
        ('EQUIPMENT_DELETED', 'Equipment Deleted'),
        # Borrowing
        ('BORROW_REQUESTED', 'Borrow Requested'),
        ('BORROW_APPROVED', 'Borrow Approved'),
        ('BORROW_REJECTED', 'Borrow Rejected'),
        ('BORROW_RETURNED', 'Borrow Returned'),
        ('BORROW_OVERDUE', 'Borrow Overdue'),
        # Reservations
        ('RESERVATION_CREATED', 'Reservation Created'),
        ('RESERVATION_CANCELLED', 'Reservation Cancelled'),
        # Consumables
        ('CONSUMABLE_USED', 'Consumable Used'),
        ('CONSUMABLE_RESTOCKED', 'Consumable Restocked'),
        # Incidents
        ('INCIDENT_REPORTED', 'Incident Reported'),
        ('INCIDENT_RESOLVED', 'Incident Resolved'),
        # Maintenance
        ('MAINTENANCE_SCHEDULED', 'Maintenance Scheduled'),
        ('MAINTENANCE_COMPLETED', 'Maintenance Completed'),
        # Users
        ('USER_REGISTERED', 'User Registered'),
        ('USER_ROLE_CHANGED', 'User Role Changed'),
        # Kits
        ('KIT_CREATED', 'Kit Created'),
        ('KIT_UPDATED', 'Kit Updated'),
        # Projects
        ('PROJECT_CREATED', 'Project Created'),
        ('PROJECT_UPDATED', 'Project Updated'),
        # Generic
        ('OTHER', 'Other'),
    ]

    actor = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activities',
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField()
    # Generic FK to related object using simple fields
    content_type_label = models.CharField(
        max_length=100, blank=True
    )  # e.g. 'equipment', 'borrowrequest'
    object_id = models.PositiveIntegerField(null=True, blank=True)
    object_repr = models.CharField(max_length=200, blank=True)  # string representation
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.actor} - {self.action} at {self.timestamp}"

    class Meta:
        ordering = ['-timestamp']
