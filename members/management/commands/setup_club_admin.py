from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from members.models import ClubApplication

class Command(BaseCommand):
    help = '为用户添加社团管理员权限'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='要添加权限的用户名')

    def handle(self, *args, **options):
        username = options['username']
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'用户 "{username}" 不存在')
            )
            return

        # 获取或创建权限
        content_type = ContentType.objects.get_for_model(ClubApplication)
        
        permissions_to_add = [
            ('can_review_club_applications', '可以审核社团申请'),
            ('can_send_interview_notifications', '可以发送笔试通知'),
            ('can_send_offer_notifications', '可以发送录取通知'),
        ]
        
        added_permissions = []
        
        for codename, name in permissions_to_add:
            permission, created = Permission.objects.get_or_create(
                codename=codename,
                content_type=content_type,
                defaults={'name': name}
            )
            
            if not user.has_perm(f'members.{codename}'):
                user.user_permissions.add(permission)
                added_permissions.append(name)
        
        # 设置为超级用户（可选）
        if not user.is_superuser:
            user.is_superuser = True
            user.is_staff = True
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f'用户 "{username}" 已设置为超级用户')
            )
        
        if added_permissions:
            self.stdout.write(
                self.style.SUCCESS(f'为用户 "{username}" 添加了以下权限:')
            )
            for perm in added_permissions:
                self.stdout.write(f'  - {perm}')
        else:
            self.stdout.write(
                self.style.WARNING(f'用户 "{username}" 已拥有所有必要权限')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'设置完成！用户 "{username}" 现在可以访问社团管理功能了')
        )