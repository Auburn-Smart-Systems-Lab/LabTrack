"""
Signal handlers for the incidents app.

- When a HIGH or CRITICAL severity IncidentReport is created or updated,
  update the related equipment's condition to DAMAGED and notify admins.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.incidents.models import IncidentReport


@receiver(post_save, sender=IncidentReport)
def update_equipment_condition_on_incident(sender, instance, created, **kwargs):
    """
    If a HIGH or CRITICAL incident is reported (or updated to that severity),
    mark the equipment condition as DAMAGED and notify admins.
    """
    if instance.severity not in ('HIGH', 'CRITICAL'):
        return

    equipment = instance.equipment

    if equipment.condition != 'DAMAGED':
        equipment.condition = 'DAMAGED'
        equipment.save(update_fields=['condition', 'updated_at'])

    if created:
        from apps.notifications.utils import notify_admins
        from apps.activity.utils import log_activity

        notify_admins(
            title=f"[{instance.get_severity_display()}] Incident Reported",
            message=(
                f"A {instance.get_severity_display().lower()} severity incident "
                f"has been reported for '{equipment.name}': {instance.title}."
            ),
            level='error' if instance.severity == 'CRITICAL' else 'warning',
        )

        log_activity(
            actor=instance.reported_by,
            action='INCIDENT_REPORTED',
            description=(
                f"Incident '{instance.title}' reported for '{equipment.name}' "
                f"with severity {instance.get_severity_display()}."
            ),
            content_type_label='incidentreport',
            object_id=instance.pk,
            object_repr=str(instance),
        )
