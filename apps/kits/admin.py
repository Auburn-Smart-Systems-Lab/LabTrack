from django.contrib import admin

from .models import Kit, KitItem


class KitItemInline(admin.TabularInline):
    model = KitItem
    extra = 1
    raw_id_fields = ('equipment',)


@admin.register(Kit)
class KitAdmin(admin.ModelAdmin):
    inlines = [KitItemInline]
    list_display = ('name', 'created_by', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name',)
    raw_id_fields = ('created_by',)
