import ssl
from django.core.mail.backends.smtp import EmailBackend as SMTPBackend


class CustomSMTPBackend(SMTPBackend):
    """
    自定义SMTP邮件后端，解决SSL证书验证失败问题
    """
    
    def open(self):
        """
        重写open方法，添加SSL上下文配置
        """
        if self.connection:
            return False
        
        # 创建SSL上下文，禁用证书验证
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # 创建连接
        from smtplib import SMTP_SSL
        self.connection = SMTP_SSL(
            self.host,
            self.port,
            timeout=self.timeout,
            context=ssl_context
        )
        
        # 如果需要认证
        if self.username and self.password:
            self.connection.login(self.username, self.password)
        
        return True 