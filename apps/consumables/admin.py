from django.contrib import admin

from .models import Consumable, ConsumableUsageLog


@admin.register(Consumable)
class ConsumableAdmin(admin.ModelAdmin):
    list_display = ('name', 'quantity', 'unit', 'low_stock_threshold', 'is_low_stock_display', 'is_active')
    list_filter = ('unit', 'is_active')
    search_fields = ('name',)

    @admin.display(boolean=True, description='Low Stock?')
    def is_low_stock_display(self, obj):
        return obj.quantity <= obj.low_stock_threshold


@admin.register(ConsumableUsageLog)
class ConsumableUsageLogAdmin(admin.ModelAdmin):
    list_display = ('consumable', 'used_by', 'quantity_used', 'timestamp')
    date_hierarchy = 'timestamp'
    raw_id_fields = ('consumable', 'used_by', 'project')
