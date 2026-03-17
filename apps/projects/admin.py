from django.contrib import admin

from .models import Project, ProjectMember


class ProjectMemberInline(admin.TabularInline):
    model = ProjectMember
    extra = 1
    raw_id_fields = ('user',)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    inlines = [ProjectMemberInline]
    list_display = ('name', 'lead', 'status', 'start_date', 'end_date')
    list_filter = ('status',)
    search_fields = ('name',)
    raw_id_fields = ('lead',)
