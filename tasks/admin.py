from django.contrib import admin
from .models import Task, Organization, UserProfile, InviteLink

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'priority', 'task_type', 'author', 'assignee', 'organization')
    list_filter = ('status', 'priority', 'task_type')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at',)

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'created_at')
    search_fields = ('name',)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'organization')
    list_filter = ('role',)

@admin.register(InviteLink)
class InviteLinkAdmin(admin.ModelAdmin):
    list_display = ('organization', 'created_by', 'is_active', 'created_at')
    list_filter = ('is_active',)