from django.contrib import admin
from .models import Member, VerificationApplication, ClubApplication
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType

# Register your models here.
@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ['user', 'oauth_id', 'identity_level', 'created_at']
    list_filter = ['identity_level', 'created_at']
    search_fields = ['user__username', 'user__email', 'oauth_id']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(VerificationApplication)
class VerificationApplicationAdmin(admin.ModelAdmin):
    list_display = ['member', 'real_name', 'identity_type', 'status', 'created_at']
    list_filter = ['identity_type', 'status', 'created_at']
    search_fields = ['member__user__username', 'real_name', 'student_id']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('member__user')

@admin.register(ClubApplication)
class ClubApplicationAdmin(admin.ModelAdmin):
    list_display = ['id', 'real_name', 'member_username', 'member_email', 'status', 'external_verified', 'created_at']
    list_filter = ['status', 'external_verified', 'created_at']
    search_fields = ['real_name', 'member__user__username', 'member__user__email']
    readonly_fields = ['created_at', 'updated_at', 'offer_uuid']
    
    def member_username(self, obj):
        return obj.member.user.username
    member_username.short_description = '用户名'
    
    def member_email(self, obj):
        return obj.member.user.email
    member_email.short_description = '邮箱'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('member__user')
    
    actions = ['send_interview_notification', 'send_offer_notification', 'reject_applications']
    
    def send_interview_notification(self, request, queryset):
        for application in queryset.filter(status='pending'):
            application.status = 'interview_sent'
            application.save()
        self.message_user(request, f"已向 {queryset.count()} 个申请发送笔试通知")
    send_interview_notification.short_description = "发送笔试通知"
    
    def send_offer_notification(self, request, queryset):
        for application in queryset.filter(status='interview_sent'):
            application.status = 'offer_sent'
            application.save()
        self.message_user(request, f"已向 {queryset.count()} 个申请发送录取通知")
    send_offer_notification.short_description = "发送录取通知"
    
    def reject_applications(self, request, queryset):
        queryset.update(status='rejected')
        self.message_user(request, f"已拒绝 {queryset.count()} 个申请")
    reject_applications.short_description = "拒绝申请"