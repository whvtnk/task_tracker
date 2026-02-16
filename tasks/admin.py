from django.contrib import admin
from .models import Task

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'status', 'priority', 'deadline', 'author')
    list_filter = ('status', 'priority', 'author')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at',)

