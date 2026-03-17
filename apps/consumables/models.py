from django.db import models


class Consumable(models.Model):
    """
    A consumable lab item (e.g. chemicals, components, materials)
    with quantity tracking and low-stock alerting.
    """

    UNIT_CHOICES = [
        ('PIECE', 'Piece'),
        ('BOX', 'Box'),
        ('PACK', 'Pack'),
        ('BOTTLE', 'Bottle'),
        ('LITER', 'Liter'),
        ('GRAM', 'Gram'),
        ('METER', 'Meter'),
        ('ROLL', 'Roll'),
        ('OTHER', 'Other'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        'equipment.Category',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='consumables',
    )
    location = models.ForeignKey(
        'equipment.Location',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='consumables',
    )
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='PIECE')
    low_stock_threshold = models.DecimalField(
        max_digits=10, decimal_places=2, default=10
    )
    unit_cost = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    supplier = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_low_stock(self):
        return self.quantity <= self.low_stock_threshold

    def __str__(self):
        return f"{self.name} ({self.quantity} {self.unit})"

    class Meta:
        ordering = ['name']


class ConsumableUsageLog(models.Model):
    """Records each usage event for a consumable, deducting from its stock."""

    consumable = models.ForeignKey(
        Consumable,
        on_delete=models.CASCADE,
        related_name='usage_logs',
    )
    used_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='consumable_usage',
    )
    quantity_used = models.DecimalField(max_digits=10, decimal_places=2)
    purpose = models.CharField(max_length=200, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"{self.consumable.name} used by {self.used_by} "
            f"on {self.timestamp.date()}"
        )

    class Meta:
        ordering = ['-timestamp']
