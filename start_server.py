#!/usr/bin/env python
"""
Django服务器启动脚本
包含错误处理和详细日志记录
"""

import os
import sys
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('django_server.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def setup_environment():
    """设置环境变量"""
    logger.info("🔧 检查环境变量...")
    
    # 只设置Django设置模块
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eidProject.settings')
    logger.info("✅ Django设置模块已设置")
    
    # 检查数据库环境变量（但不强制设置）
    db_vars = ['DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_NAME', 'DB_PORT']
    missing_vars = []
    
    for var in db_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.warning(f"⚠️  以下数据库环境变量未设置: {', '.join(missing_vars)}")
        logger.info("将使用settings.py中的默认值")
        logger.info("如需自定义数据库配置，请设置相应的环境变量")
    else:
        logger.info("✅ 所有数据库环境变量已设置")
    
    return True

def check_dependencies():
    """检查依赖项"""
    logger.info("🔍 检查依赖项...")
    
    try:
        import django
        import pymysql
        import oauth2_provider
        import requests
        import whitenoise
        logger.info("✅ 所有依赖项已安装")
        return True
    except ImportError as e:
        logger.error(f"❌ 缺少依赖项: {e}")
        logger.error("请运行: pip install -r requirements.txt")
        return False

def run_migrations():
    """运行数据库迁移"""
    logger.info("🔄 运行数据库迁移...")
    
    try:
        os.system("python manage.py migrate --noinput")
        logger.info("✅ 数据库迁移完成")
        return True
    except Exception as e:
        logger.error(f"❌ 数据库迁移失败: {e}")
        return False

def collect_static():
    """收集静态文件"""
    logger.info("📁 收集静态文件...")
    
    try:
        os.system("python manage.py collectstatic --noinput")
        logger.info("✅ 静态文件收集完成")
        return True
    except Exception as e:
        logger.error(f"❌ 静态文件收集失败: {e}")
        return False

def start_server():
    """启动Django服务器"""
    logger.info("🚀 启动Django服务器...")
    
    try:
        # 使用gunicorn启动（如果可用）
        try:
            import gunicorn
            logger.info("使用gunicorn启动服务器...")
            os.system("gunicorn eidProject.wsgi:application --bind 0.0.0.0:8000 --workers 3")
        except ImportError:
            logger.info("使用Django开发服务器启动...")
            os.system("python manage.py runserver 0.0.0.0:8000")
        
    except KeyboardInterrupt:
        logger.info("🛑 服务器已停止")
    except Exception as e:
        logger.error(f"❌ 服务器启动失败: {e}")

def main():
    """主函数"""
    logger.info("🚀 Django服务器启动工具")
    logger.info("=" * 50)
    
    # 设置环境
    if not setup_environment():
        sys.exit(1)
    
    # 检查依赖项
    if not check_dependencies():
        sys.exit(1)
    
    # 运行迁移
    if not run_migrations():
        logger.warning("⚠️  迁移失败，但继续启动服务器...")
    
    # 收集静态文件
    if not collect_static():
        logger.warning("⚠️  静态文件收集失败，但继续启动服务器...")
    
    # 启动服务器
    start_server()

if __name__ == '__main__':
    main() 