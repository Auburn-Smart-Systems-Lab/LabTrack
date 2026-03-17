from django.db import models


class Kit(models.Model):
    """A curated bundle of equipment items that can be borrowed together."""

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_kits',
    )
    is_active = models.BooleanField(default=True)
    is_shared = models.BooleanField(default=False, help_text='Make this kit visible and borrowable by all members.')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class KitItem(models.Model):
    """A single equipment item included in a Kit, with optional quantity."""

    kit = models.ForeignKey(Kit, on_delete=models.CASCADE, related_name='items')
    equipment = models.ForeignKey(
        'equipment.Equipment',
        on_delete=models.CASCADE,
        related_name='kit_memberships',
    )
    quantity = models.PositiveIntegerField(default=1)
    notes = models.CharField(max_length=200, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.equipment.name} in {self.kit.name}"

    class Meta:
        unique_together = ['kit', 'equipment']
