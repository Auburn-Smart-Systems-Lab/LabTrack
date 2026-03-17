from django.contrib import admin

from .models import Category, Equipment, LifecycleEvent, Location, MovementLog


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'building', 'room')
    search_fields = ('name', 'building')


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'location', 'status', 'condition', 'owner', 'created_at')
    list_filter = ('status', 'condition', 'category', 'location')
    search_fields = ('name', 'serial_number', 'model_number')
    raw_id_fields = ('owner',)
    date_hierarchy = 'created_at'


@admin.register(LifecycleEvent)
class LifecycleEventAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'event_type', 'performed_by', 'timestamp')
    list_filter = ('event_type',)
    search_fields = ('equipment__name',)
    raw_id_fields = ('equipment', 'performed_by')


@admin.register(MovementLog)
class MovementLogAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'from_location', 'to_location', 'moved_by', 'timestamp')
    raw_id_fields = ('equipment', 'moved_by')
