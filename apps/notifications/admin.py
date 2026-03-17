from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'title', 'level', 'is_read', 'created_at')
    list_filter = ('level', 'is_read')
    search_fields = ('recipient__email', 'title')
    raw_id_fields = ('recipient',)
