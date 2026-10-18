from django.contrib import admin, messages
from django.utils import timezone
from .models import Member, VerificationApplication, ClubApplication
from .views import (send_interview_email, send_interview_invite_email,
                    send_offer_email)
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
    
    actions = ['send_interview_notification', 'send_interview_invite_notification',
               'send_offer_notification', 'reject_applications']

    def _report_bulk_send(self, request, label, sent, failed):
        message = f"已向 {sent} 个申请发送{label}"
        if failed:
            message += f"，{failed} 个发送失败（请检查邮件配置后重发）"
        self.message_user(
            request, message,
            level=messages.WARNING if failed else messages.SUCCESS,
        )

    def send_interview_notification(self, request, queryset):
        sent = failed = 0
        targets = queryset.filter(status='pending').select_related('member__user')
        for application in targets:
            if send_interview_email(application.member.user.email, application.real_name):
                application.status = 'interview_sent'
                application.interview_sent_at = timezone.now()
                application.save(update_fields=['status', 'interview_sent_at', 'updated_at'])
                sent += 1
            else:
                failed += 1
        self._report_bulk_send(request, '笔试通知', sent, failed)
    send_interview_notification.short_description = "发送笔试通知"

    def send_interview_invite_notification(self, request, queryset):
        sent = failed = 0
        targets = queryset.filter(status='interview_sent').select_related('member__user')
        for application in targets:
            if send_interview_invite_email(application.member.user.email, application.real_name):
                application.status = 'interview_invited'
                application.interview_invited_at = timezone.now()
                application.save(update_fields=['status', 'interview_invited_at', 'updated_at'])
                sent += 1
            else:
                failed += 1
        self._report_bulk_send(request, '面试通知', sent, failed)
    send_interview_invite_notification.short_description = "发送面试通知"

    def send_offer_notification(self, request, queryset):
        sent = failed = 0
        targets = queryset.filter(status='interview_invited').select_related('member__user')
        for application in targets:
            if send_offer_email(application.member.user.email, application.real_name,
                                str(application.offer_uuid)):
                application.status = 'offer_sent'
                application.offer_sent_at = timezone.now()
                application.save(update_fields=['status', 'offer_sent_at', 'updated_at'])
                sent += 1
            else:
                failed += 1
        self._report_bulk_send(request, '录取通知', sent, failed)
    send_offer_notification.short_description = "发送录取通知"
    
    def reject_applications(self, request, queryset):
        queryset.update(status='rejected')
        self.message_user(request, f"已拒绝 {queryset.count()} 个申请")
    reject_applications.short_description = "拒绝申请"