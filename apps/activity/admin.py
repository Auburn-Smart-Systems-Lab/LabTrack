from django.contrib import admin

from .models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('actor', 'action', 'description', 'timestamp')
    list_filter = ('action',)
    search_fields = ('actor__email', 'description')
    readonly_fields = ('timestamp', 'ip_address')
    date_hierarchy = 'timestamp'
    raw_id_fields = ('actor',)
