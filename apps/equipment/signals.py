"""
Signal handlers for the equipment app.
When Equipment status or condition changes, a LifecycleEvent is automatically created.
"""

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from apps.equipment.models import Equipment, LifecycleEvent


@receiver(pre_save, sender=Equipment)
def capture_previous_equipment_state(sender, instance, **kwargs):
    """
    Before saving, attach the previous status and condition to the instance
    so the post_save handler can compare old vs new values.
    """
    if instance.pk:
        try:
            previous = Equipment.objects.get(pk=instance.pk)
            instance._previous_status = previous.status
            instance._previous_condition = previous.condition
        except Equipment.DoesNotExist:
            instance._previous_status = None
            instance._previous_condition = None
    else:
        instance._previous_status = None
        instance._previous_condition = None


@receiver(post_save, sender=Equipment)
def create_lifecycle_event_on_status_change(sender, instance, created, **kwargs):
    """
    After saving Equipment, create a LifecycleEvent when status or condition
    has changed. On creation, log a DEPLOYED event.
    """
    if created:
        LifecycleEvent.objects.create(
            equipment=instance,
            event_type='DEPLOYED',
            description=(
                f"Equipment '{instance.name}' added to inventory with status "
                f"'{instance.get_status_display()}' and condition "
                f"'{instance.get_condition_display()}'."
            ),
            performed_by=instance.owner,
        )
        return

    previous_status = getattr(instance, '_previous_status', None)
    previous_condition = getattr(instance, '_previous_condition', None)

    if previous_status is not None and previous_status != instance.status:
        LifecycleEvent.objects.create(
            equipment=instance,
            event_type='STATUS_CHANGE',
            description=(
                f"Status changed from '{previous_status}' "
                f"to '{instance.get_status_display()}'."
            ),
        )

    if previous_condition is not None and previous_condition != instance.condition:
        LifecycleEvent.objects.create(
            equipment=instance,
            event_type='CONDITION_CHANGE',
            description=(
                f"Condition changed from '{previous_condition}' "
                f"to '{instance.get_condition_display()}'."
            ),
        )
