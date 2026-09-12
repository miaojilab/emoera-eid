from django.db import models
from django.contrib.auth.models import User
import uuid

# identity_type（VerificationApplication.IDENTITY_CHOICES 的 key）→ Member.identity_level
IDENTITY_TYPE_TO_LEVEL = {
    'active': 1,      # 活跃成员
    'core': 2,        # 核心成员
    'key': 3,         # 核心贡献
    'management': 4,  # 管理层
    'outstanding': 5, # 卓越贡献
    'smart_car': 6,   # 智能车团队
}

class Member(models.Model):
    IDENTITY_LEVELS = [
        (0, '未认证'),
        (1, '活跃成员'),
        (2, '核心成员'),
        (3, '核心贡献'),
        (4, '管理层'),
        (5, '卓越贡献'),
        (6, '智能车团队'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # OIDC sub 为字符串（可能是 UUID/长数字串），用 CharField 兼容；旧的纯数字值可无损存储
    oauth_id = models.CharField(max_length=64, unique=True)
    phone = models.CharField(max_length=20, blank=True, default='')
    avatar = models.URLField(max_length=255, blank=True, default='')
    bio = models.TextField(blank=True, default='')
    identity_level = models.IntegerField(choices=IDENTITY_LEVELS, default=0)
    identity_title = models.CharField(max_length=100, blank=True, default='')  # 认证的身份名称
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_identity_card_image(self):
        return f'https://esd-id.emoera.com/images/level_{self.identity_level}.png'

    def __str__(self):
        return self.user.username 

class VerificationApplication(models.Model):
    IDENTITY_CHOICES = [
        ('outstanding', '卓越贡献'),
        ('core', '核心成员'),
        ('active', '活跃成员'),
        ('management', '管理层'),
        ('key', '核心贡献'),
        ('smart_car', '智能车团队'),
    ]
    
    STATUS_CHOICES = [
        ('pending', '待审核'),
        ('approved', '已通过'),
        ('rejected', '已拒绝'),
    ]
    
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    real_name = models.CharField(max_length=50, verbose_name='姓名')
    student_id = models.CharField(max_length=20, verbose_name='学号')
    identity_title = models.CharField(max_length=100, verbose_name='认证身份')
    identity_type = models.CharField(
        max_length=20, 
        choices=IDENTITY_CHOICES,
        verbose_name='身份类型'
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='审核状态'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '认证申请'
        verbose_name_plural = '认证申请'
        permissions = [
            ("can_review_applications", "Can review verification applications"),
        ]


class ClubApplication(models.Model):
    """社团报名申请"""
    STATUS_CHOICES = [
        ('pending', '待审核'),
        ('interview_sent', '笔试通知已发送'),
        ('offer_sent', '录取通知已发送'),
        ('offer_confirmed', 'Offer已确认'),
        ('rejected', '已拒绝'),
    ]
    
    member = models.ForeignKey(Member, on_delete=models.CASCADE, verbose_name='成员')
    real_name = models.CharField(max_length=50, verbose_name='真实姓名')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='申请状态'
    )
    # 外部认证状态检查结果
    external_verification_status = models.CharField(max_length=50, blank=True, verbose_name='外部认证状态')
    external_verified = models.BooleanField(default=False, verbose_name='外部认证通过')
    
    # Offer确认相关
    offer_uuid = models.UUIDField(default=uuid.uuid4, unique=True, verbose_name='Offer确认码')
    offer_confirmed_at = models.DateTimeField(null=True, blank=True, verbose_name='Offer确认时间')
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='申请时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    interview_sent_at = models.DateTimeField(null=True, blank=True, verbose_name='笔试通知发送时间')
    offer_sent_at = models.DateTimeField(null=True, blank=True, verbose_name='录取通知发送时间')
    
    class Meta:
        verbose_name = '社团报名申请'
        verbose_name_plural = '社团报名申请'
        permissions = [
            ("can_review_club_applications", "Can review club applications"),
            ("can_send_interview_notifications", "Can send interview notifications"),
            ("can_send_offer_notifications", "Can send offer notifications"),
        ]
    
    def __str__(self):
        return f"{self.real_name} - {self.get_status_display()}" 