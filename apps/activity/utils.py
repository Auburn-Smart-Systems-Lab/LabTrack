"""
Utility helpers for logging activity across the application.
"""


def log_activity(
    actor,
    action,
    description,
    content_type_label='',
    object_id=None,
    object_repr='',
    request=None,
):
    """
    Create an ActivityLog entry.

    Call this from views or signals whenever a significant action occurs.

    Args:
        actor:              CustomUser instance (or None for system actions).
        action:             One of ActivityLog.ACTION_CHOICES values.
        description:        Human-readable description of what happened.
        content_type_label: String label for the related model (e.g. 'equipment').
        object_id:          Primary key of the related object.
        object_repr:        String representation of the related object.
        request:            Django HttpRequest (used to extract IP address).
    """
    from apps.activity.models import ActivityLog

    ip = None
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')

    ActivityLog.objects.create(
        actor=actor,
        action=action,
        description=description,
        content_type_label=content_type_label,
        object_id=object_id,
        object_repr=object_repr,
        ip_address=ip,
    )
