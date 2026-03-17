from django.contrib import admin

from .models import CalibrationLog, IncidentReport, MaintenanceLog


@admin.register(IncidentReport)
class IncidentReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'equipment', 'reported_by', 'severity', 'status', 'created_at')
    list_filter = ('severity', 'status')
    search_fields = ('title', 'equipment__name')
    raw_id_fields = ('equipment', 'reported_by', 'resolved_by')


@admin.register(MaintenanceLog)
class MaintenanceLogAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'maintenance_type', 'status', 'scheduled_date', 'completed_date')
    list_filter = ('maintenance_type', 'status')
    search_fields = ('equipment__name',)
    raw_id_fields = ('equipment', 'performed_by')


@admin.register(CalibrationLog)
class CalibrationLogAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'calibrated_by', 'calibration_date', 'next_calibration_date', 'status')
    list_filter = ('status',)
    search_fields = ('equipment__name',)
    raw_id_fields = ('equipment', 'calibrated_by')
