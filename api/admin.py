from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Project, TimeEntry


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Custom User admin with email verification fields"""
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_email_verified', 'is_active', 'date_joined')
    list_filter = ('is_email_verified', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Email Verification', {'fields': ('is_email_verified', 'email_verification_token')}),
    )
    
    readonly_fields = ('email_verification_token', 'date_joined', 'last_login')


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Project admin with user filtering and search"""
    list_display = ('name', 'user', 'color', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at', 'user')
    search_fields = ('name', 'description', 'user__email', 'user__username')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'user')
        }),
        ('Appearance', {
            'fields': ('color',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    """TimeEntry admin with comprehensive display and filtering"""
    list_display = ('user', 'project', 'description_short', 'start_time', 'end_time', 'duration_formatted', 'status')
    list_filter = ('status', 'start_time', 'project', 'user')
    search_fields = ('description', 'user__email', 'user__username', 'project__name')
    ordering = ('-start_time',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'project', 'description')
        }),
        ('Time Tracking', {
            'fields': ('start_time', 'end_time', 'duration_seconds', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('duration_seconds', 'created_at', 'updated_at')
    
    def description_short(self, obj):
        """Show truncated description in list view"""
        if obj.description:
            return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
        return '-'
    description_short.short_description = 'Description'
    
    def get_queryset(self, request):
        """Optimize queries with select_related"""
        return super().get_queryset(request).select_related('user', 'project')