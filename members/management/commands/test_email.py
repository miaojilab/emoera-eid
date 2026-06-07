from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.utils.html import strip_tags

class Command(BaseCommand):
    help = '测试邮件发送功能'

    def add_arguments(self, parser):
        parser.add_argument(
            '--to',
            type=str,
            help='收件人邮箱地址',
            default='test@example.com'
        )

    def handle(self, *args, **options):
        to_email = options['to']
        
        self.stdout.write("=== Django邮件配置测试 ===")
        self.stdout.write(f"邮件后端: {settings.EMAIL_BACKEND}")
        self.stdout.write(f"SMTP主机: {settings.EMAIL_HOST}")
        self.stdout.write(f"SMTP端口: {settings.EMAIL_PORT}")
        self.stdout.write(f"使用SSL: {settings.EMAIL_USE_SSL}")
        self.stdout.write(f"发件人: {settings.DEFAULT_FROM_EMAIL}")
        self.stdout.write("=" * 30)
        
        # 测试邮件内容
        subject = 'Django邮件配置测试'
        html_message = '''
        <h2>邮件配置测试</h2>
        <p>如果您收到这封邮件，说明Django邮件配置正确！</p>
        <p>测试时间：<strong>现在</strong></p>
        <hr>
        <p><em>这是一封测试邮件，请忽略。</em></p>
        '''
        plain_message = strip_tags(html_message)
        
        try:
            self.stdout.write(f"正在向 {to_email} 发送测试邮件...")
            
            result = send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to_email],
                html_message=html_message,
                fail_silently=False,
            )
            
            if result == 1:
                self.stdout.write(
                    self.style.SUCCESS("✅ 邮件发送成功！")
                )
            else:
                self.stdout.write(
                    self.style.WARNING("⚠️ 邮件发送可能失败")
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ 邮件发送失败: {str(e)}")
            )
            self.stdout.write("\n可能的原因：")
            self.stdout.write("1. SMTP服务器配置错误")
            self.stdout.write("2. 用户名或密码不正确")
            self.stdout.write("3. 网络连接问题")
            self.stdout.write("4. 邮箱服务商限制")
            self.stdout.write("5. 防火墙阻止SMTP连接")
            
            # 输出详细错误信息
            import traceback
            self.stdout.write("\n详细错误信息：")
            self.stdout.write(traceback.format_exc())