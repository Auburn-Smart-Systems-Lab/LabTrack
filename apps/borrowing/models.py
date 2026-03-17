from django.db import models


class BorrowRequest(models.Model):
    """
    Represents a request by a lab member to borrow equipment or a kit.
    Tracks the full lifecycle from PENDING through RETURNED or OVERDUE.
    """

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('ACTIVE', 'Active'),       # approved and item picked up
        ('RETURNED', 'Returned'),
        ('OVERDUE', 'Overdue'),
        ('CANCELLED', 'Cancelled'),
    ]

    borrower = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.CASCADE,
        related_name='borrow_requests',
    )
    equipment = models.ForeignKey(
        'equipment.Equipment',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='borrow_requests',
    )
    kit = models.ForeignKey(
        'kits.Kit',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='borrow_requests',
    )
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='borrow_requests',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    purpose = models.TextField()
    requested_date = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_borrows',
    )
    approved_date = models.DateTimeField(null=True, blank=True)
    due_date = models.DateField()
    returned_date = models.DateTimeField(null=True, blank=True)
    return_condition = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        item = self.equipment or self.kit
        return f"{self.borrower.username} borrowed {item} ({self.status})"

    @property
    def is_overdue(self):
        from django.utils import timezone
        from datetime import date
        return self.status in ['ACTIVE', 'APPROVED'] and self.due_date < date.today()

    @property
    def item(self):
        return self.equipment or self.kit

    class Meta:
        ordering = ['-requested_date']
