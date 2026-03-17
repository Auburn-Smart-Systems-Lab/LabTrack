"""
Signal handlers for the consumables app.

- When a ConsumableUsageLog is created, subtract the used quantity from the
  Consumable's stock.
- If the resulting quantity falls at or below the low_stock_threshold, notify admins.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.consumables.models import ConsumableUsageLog


@receiver(post_save, sender=ConsumableUsageLog)
def deduct_consumable_quantity(sender, instance, created, **kwargs):
    """
    On creation of a ConsumableUsageLog:
    1. Subtract quantity_used from the related Consumable's quantity.
    2. If low stock is detected, notify admins.
    """
    if not created:
        return

    consumable = instance.consumable

    # Deduct quantity (prevent going below zero)
    consumable.quantity = max(
        consumable.quantity - instance.quantity_used,
        0,
    )
    consumable.save(update_fields=['quantity', 'updated_at'])

    # Notify admins if stock is now low
    if consumable.is_low_stock:
        from apps.notifications.utils import notify_admins

        notify_admins(
            title='Low Stock Alert',
            message=(
                f"Consumable '{consumable.name}' is running low. "
                f"Current stock: {consumable.quantity} {consumable.get_unit_display()} "
                f"(threshold: {consumable.low_stock_threshold})."
            ),
            level='warning',
        )
