from django.contrib import admin

from .models import Reservation, WaitlistEntry


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('requester', 'equipment', 'kit', 'status', 'start_date', 'end_date')
    list_filter = ('status',)
    raw_id_fields = ('requester', 'equipment', 'kit')


@admin.register(WaitlistEntry)
class WaitlistEntryAdmin(admin.ModelAdmin):
    list_display = ('user', 'equipment', 'kit', 'position', 'notified', 'created_at')
    raw_id_fields = ('user', 'equipment', 'kit')
