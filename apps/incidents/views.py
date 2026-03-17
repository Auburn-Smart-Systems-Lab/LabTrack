"""Views for the incidents app."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.accounts.decorators import admin_required
from apps.activity.utils import log_activity
from apps.incidents.forms import (
    CalibrationLogForm,
    IncidentReportForm,
    IncidentUpdateForm,
    MaintenanceCompleteForm,
    MaintenanceLogForm,
)
from apps.incidents.models import CalibrationLog, IncidentReport, MaintenanceLog
from apps.notifications.utils import notify, notify_admins


# ---------------------------------------------------------------------------
# Incident views
# ---------------------------------------------------------------------------

@login_required
def incident_list_view(request):
    """Members see their own reported incidents; admins see all."""
    if request.user.role == 'ADMIN':
        incidents = IncidentReport.objects.select_related(
            'equipment', 'reported_by'
        ).order_by('-created_at')
    else:
        incidents = IncidentReport.objects.filter(
            reported_by=request.user
        ).select_related('equipment', 'reported_by').order_by('-created_at')

    paginator = Paginator(incidents, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'incidents/list.html', {
        'page_obj': page_obj,
    })


@login_required
def incident_detail_view(request, pk):
    """Show full details of a single incident report."""
    incident = get_object_or_404(IncidentReport, pk=pk)

    # Members can only view their own incidents
    if request.user.role != 'ADMIN' and incident.reported_by != request.user:
        messages.error(request, 'You do not have permission to view this incident.')
        return redirect('incidents:list')

    return render(request, 'incidents/detail.html', {'incident': incident})


@login_required
def incident_create_view(request):
    """Any logged-in user can report a new incident."""
    if request.method == 'POST':
        form = IncidentReportForm(request.POST, request.FILES)
        if form.is_valid():
            incident = form.save(commit=False)
            incident.reported_by = request.user
            incident.save()

            log_activity(
                actor=request.user,
                action='INCIDENT_REPORTED',
                description=(
                    f'{request.user.username} reported incident "{incident.title}" '
                    f'on {incident.equipment.name} (severity: {incident.severity}).'
                ),
                content_type_label='incidentreport',
                object_id=incident.pk,
                object_repr=str(incident),
                request=request,
            )

            notify_admins(
                title=f'New Incident Reported: {incident.title}',
                message=(
                    f'{request.user.username} reported a {incident.get_severity_display()} '
                    f'incident on "{incident.equipment.name}": {incident.title}.'
                ),
                level='warning' if incident.severity in ('HIGH', 'CRITICAL') else 'info',
                link=f'/incidents/{incident.pk}/',
            )

            messages.success(request, 'Incident reported successfully.')
            return redirect('incidents:detail', pk=incident.pk)
    else:
        form = IncidentReportForm()

    return render(request, 'incidents/form.html', {
        'form': form,
        'title': 'Report Incident',
        'submit_label': 'Submit Report',
    })


@login_required
def incident_edit_view(request, pk):
    """The reporter or an admin can edit an incident report."""
    incident = get_object_or_404(IncidentReport, pk=pk)

    if request.user.role != 'ADMIN' and incident.reported_by != request.user:
        messages.error(request, 'You do not have permission to edit this incident.')
        return redirect('incidents:detail', pk=pk)

    if request.method == 'POST':
        form = IncidentReportForm(request.POST, request.FILES, instance=incident)
        if form.is_valid():
            incident = form.save()
            log_activity(
                actor=request.user,
                action='INCIDENT_REPORTED',
                description=f'Incident "{incident.title}" updated by {request.user.username}.',
                content_type_label='incidentreport',
                object_id=incident.pk,
                object_repr=str(incident),
                request=request,
            )
            messages.success(request, 'Incident updated successfully.')
            return redirect('incidents:detail', pk=incident.pk)
    else:
        form = IncidentReportForm(instance=incident)

    return render(request, 'incidents/form.html', {
        'form': form,
        'incident': incident,
        'title': f'Edit Incident: {incident.title}',
        'submit_label': 'Save Changes',
    })


@admin_required
def incident_resolve_view(request, pk):
    """Admin only: resolve an incident, optionally updating equipment condition."""
    incident = get_object_or_404(IncidentReport, pk=pk)

    if request.method == 'POST':
        form = IncidentUpdateForm(request.POST, instance=incident)
        if form.is_valid():
            incident = form.save(commit=False)
            if incident.status == 'RESOLVED':
                incident.resolved_by = request.user
                incident.resolved_at = timezone.now()

                # Update equipment condition if incident was critical
                if incident.severity == 'CRITICAL':
                    equipment = incident.equipment
                    equipment.condition = 'POOR'
                    equipment.save(update_fields=['condition', 'updated_at'])
            incident.save()

            log_activity(
                actor=request.user,
                action='INCIDENT_RESOLVED',
                description=(
                    f'Incident "{incident.title}" marked as {incident.get_status_display()} '
                    f'by {request.user.username}.'
                ),
                content_type_label='incidentreport',
                object_id=incident.pk,
                object_repr=str(incident),
                request=request,
            )

            if incident.reported_by:
                notify(
                    recipient=incident.reported_by,
                    title=f'Incident Update: {incident.title}',
                    message=(
                        f'Your incident report "{incident.title}" has been marked as '
                        f'{incident.get_status_display()}.'
                    ),
                    level='success' if incident.status == 'RESOLVED' else 'info',
                    link=f'/incidents/{incident.pk}/',
                )

            messages.success(request, f'Incident updated to "{incident.get_status_display()}".')
            return redirect('incidents:detail', pk=incident.pk)
    else:
        form = IncidentUpdateForm(instance=incident)

    return render(request, 'incidents/resolve.html', {
        'form': form,
        'incident': incident,
    })


# ---------------------------------------------------------------------------
# Maintenance views
# ---------------------------------------------------------------------------

@login_required
def maintenance_list_view(request):
    """Admins see all maintenance logs; members see logs for equipment they own or borrowed."""
    if request.user.role == 'ADMIN':
        logs = MaintenanceLog.objects.select_related(
            'equipment', 'performed_by'
        ).order_by('-scheduled_date')
    else:
        owned_equipment_ids = request.user.owned_equipment.values_list('pk', flat=True)
        borrowed_equipment_ids = (
            request.user.borrow_requests
            .filter(status__in=['APPROVED', 'ACTIVE'])
            .exclude(equipment__isnull=True)
            .values_list('equipment__pk', flat=True)
        )
        all_ids = list(owned_equipment_ids) + list(borrowed_equipment_ids)
        logs = MaintenanceLog.objects.filter(
            equipment__pk__in=all_ids
        ).select_related('equipment', 'performed_by').order_by('-scheduled_date')

    paginator = Paginator(logs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'incidents/maintenance_list.html', {'page_obj': page_obj})


@login_required
def maintenance_detail_view(request, pk):
    """Show details of a single maintenance log entry."""
    log = get_object_or_404(MaintenanceLog, pk=pk)
    return render(request, 'incidents/maintenance_detail.html', {'log': log})


@admin_required
def maintenance_create_view(request):
    """Admin only: schedule a new maintenance activity."""
    if request.method == 'POST':
        form = MaintenanceLogForm(request.POST)
        if form.is_valid():
            log = form.save(commit=False)
            log.performed_by = request.user
            log.save()

            log_activity(
                actor=request.user,
                action='MAINTENANCE_SCHEDULED',
                description=(
                    f'Maintenance scheduled for "{log.equipment.name}" '
                    f'({log.get_maintenance_type_display()}) on {log.scheduled_date}.'
                ),
                content_type_label='maintenancelog',
                object_id=log.pk,
                object_repr=str(log),
                request=request,
            )

            notify_admins(
                title=f'Maintenance Scheduled: {log.equipment.name}',
                message=(
                    f'{log.get_maintenance_type_display()} maintenance scheduled for '
                    f'"{log.equipment.name}" on {log.scheduled_date}.'
                ),
                level='info',
                link=f'/incidents/maintenance/{log.pk}/',
            )

            messages.success(request, 'Maintenance log created successfully.')
            return redirect('incidents:maintenance_detail', pk=log.pk)
    else:
        form = MaintenanceLogForm()

    return render(request, 'incidents/maintenance_form.html', {
        'form': form,
        'title': 'Schedule Maintenance',
        'submit_label': 'Create',
    })


@admin_required
def maintenance_complete_view(request, pk):
    """Admin only: mark a maintenance log as completed and update equipment status."""
    log = get_object_or_404(MaintenanceLog, pk=pk)

    if request.method == 'POST':
        form = MaintenanceCompleteForm(request.POST, instance=log)
        if form.is_valid():
            log = form.save(commit=False)
            if log.status == 'COMPLETED':
                # Set equipment back to available
                equipment = log.equipment
                if equipment.status == 'MAINTENANCE':
                    equipment.status = 'AVAILABLE'
                    equipment.save(update_fields=['status', 'updated_at'])
            log.save()

            log_activity(
                actor=request.user,
                action='MAINTENANCE_COMPLETED',
                description=(
                    f'Maintenance for "{log.equipment.name}" marked as '
                    f'{log.get_status_display()} by {request.user.username}.'
                ),
                content_type_label='maintenancelog',
                object_id=log.pk,
                object_repr=str(log),
                request=request,
            )

            messages.success(request, f'Maintenance log updated to "{log.get_status_display()}".')
            return redirect('incidents:maintenance_detail', pk=log.pk)
    else:
        form = MaintenanceCompleteForm(instance=log)

    return render(request, 'incidents/maintenance_complete.html', {
        'form': form,
        'log': log,
    })


# ---------------------------------------------------------------------------
# Calibration views
# ---------------------------------------------------------------------------

@login_required
def calibration_list_view(request):
    """List all calibration logs; admins see all, members see their equipment."""
    if request.user.role == 'ADMIN':
        logs = CalibrationLog.objects.select_related(
            'equipment', 'calibrated_by'
        ).order_by('-calibration_date')
    else:
        owned_equipment_ids = request.user.owned_equipment.values_list('pk', flat=True)
        logs = CalibrationLog.objects.filter(
            equipment__pk__in=owned_equipment_ids
        ).select_related('equipment', 'calibrated_by').order_by('-calibration_date')

    paginator = Paginator(logs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'incidents/calibration_list.html', {'page_obj': page_obj})


@admin_required
def calibration_create_view(request):
    """Admin only: record a new calibration log."""
    if request.method == 'POST':
        form = CalibrationLogForm(request.POST)
        if form.is_valid():
            calibration = form.save(commit=False)
            calibration.calibrated_by = request.user
            calibration.save()

            log_activity(
                actor=request.user,
                action='OTHER',
                description=(
                    f'Calibration logged for "{calibration.equipment.name}" '
                    f'on {calibration.calibration_date} — status: {calibration.get_status_display()}.'
                ),
                content_type_label='calibrationlog',
                object_id=calibration.pk,
                object_repr=str(calibration),
                request=request,
            )

            notify_admins(
                title=f'Calibration Logged: {calibration.equipment.name}',
                message=(
                    f'Calibration for "{calibration.equipment.name}" recorded on '
                    f'{calibration.calibration_date}. Status: {calibration.get_status_display()}.'
                ),
                level='success' if calibration.status == 'PASS' else 'warning',
                link=f'/incidents/calibration/',
            )

            messages.success(request, 'Calibration log created successfully.')
            return redirect('incidents:calibration_list')
    else:
        form = CalibrationLogForm()

    return render(request, 'incidents/calibration_form.html', {
        'form': form,
        'title': 'Record Calibration',
        'submit_label': 'Save',
    })
