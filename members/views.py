from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.conf import settings
import requests
import json
import logging
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .models import Member, VerificationApplication, ClubApplication
import uuid
from urllib.parse import urlencode
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
import secrets
import string
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)

def oauth_login(request):
    """初始化 OAuth2 登录流程"""
    oauth_params = {
        'client_id': settings.OAUTH2_PROVIDER['CLIENT_ID'],
        'response_type': 'token',
        'redirect_uri': settings.OAUTH_CALLBACK_URL,
        'scope': 'read',
        'state': str(uuid.uuid4())  # 生成随机 state 用于防止 CSRF
    }
    
    # 将 state 保存在 session 中
    request.session['oauth_state'] = oauth_params['state']
    
    # 构建授权 URL
    auth_url = f"{settings.OAUTH2_PROVIDER['OAUTH2_SERVER_URL']}/oauth/authorize?{urlencode(oauth_params)}"
    return redirect(auth_url)

def oauth_callback(request):
    return render(request, 'members/callback.html')

@csrf_exempt
@require_http_methods(["POST"])
def save_token(request):
    """处理前端传来的 access_token"""
    try:
        data = json.loads(request.body)
        access_token = data.get('access_token')
        state = data.get('state')
        # 验证 state 防止 CSRF
        if state != request.session.get('oauth_state'):
            logger.warning("OAuth state validation failed")
            return JsonResponse({'status': 'error', 'message': 'Invalid state'}, status=400)
        
        if access_token:
            user_info = get_oauth_user_info(access_token)
            if user_info:
                user = create_or_update_user(user_info)
                # 使用 Django 的默认认证后端进行登录
                auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                return JsonResponse({'status': 'success', 'redirect_url': '/profile/'})
            
        return JsonResponse({'status': 'error', 'message': '获取用户信息失败'}, status=400)
    except Exception as e:
        logger.exception("Failed to process OAuth token")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

def get_oauth_user_info(access_token):
    """获取用户信息"""
    api_url = f"{settings.OAUTH2_PROVIDER['OAUTH2_API_URL']}/api/oauth2/userinfo"
    
    # 将 access_token 作为查询参数而不是 header
    params = {
        'client_id': settings.OAUTH2_PROVIDER['CLIENT_ID'],
        'client_secret': settings.OAUTH2_PROVIDER['CLIENT_SECRET'],
        'access_token': access_token
    }
    
    try:
        response = requests.get(api_url, params=params)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 200:  # 检查 API 响应状态
                return result.get('data')
            logger.warning("OAuth userinfo API returned an error: %s", result.get('message'))
    except Exception as e:
        logger.exception("Failed to fetch OAuth user info")
    return None

def create_or_update_user(user_info):
    """创建或更新本地用户"""
    oauth_id = user_info['id']
    username = user_info['username']
    
    try:
        # 首先尝试通过 oauth_id 查找用户
        member = Member.objects.get(oauth_id=oauth_id)
        user = member.user
    except Member.DoesNotExist:
        try:
            # 如果找不到 member，尝试通过用户名查找用户
            user = User.objects.get(username=username)
            # 如果找到用户，为其创建 member
            member = Member.objects.create(
                user=user,
                oauth_id=oauth_id,
                avatar=user_info.get('avatar') or '',
                bio=user_info.get('bio') or ''
            )
        except User.DoesNotExist:
            # 如果用户也不存在，才创建新用户
            # 生成一个随机密码
            alphabet = string.ascii_letters + string.digits + string.punctuation
            password = ''.join(secrets.choice(alphabet) for i in range(16))
            
            user = User.objects.create_user(
                username=username,
                email=user_info.get('email', ''),
                password=password
            )
            # 创建新的 Member
            member = Member.objects.create(
                user=user,
                oauth_id=oauth_id,
                avatar=user_info.get('avatar') or '',
                bio=user_info.get('bio') or ''
            )
    
    # 更新用户信息
    user.email = user_info.get('email', '')
    user.save()
    
    # 更新 Member 信息
    member.avatar = user_info.get('avatar') or ''
    member.bio = user_info.get('bio') or ''
    member.save()
    
    return user

@login_required
def member_profile(request):
    """显示会员资料"""
    try:
        member = Member.objects.get(user=request.user)
        return render(request, 'members/profile.html', {
            'user_info': {
                'username': request.user.username,
                'email': request.user.email,
                'avatar': request.user.member.avatar if hasattr(request.user, 'member') else None,
                'bio': request.user.member.bio if hasattr(request.user, 'member') else '',
                'createdAt': request.user.date_joined,
            }
        })
    except Member.DoesNotExist:
        return redirect('login') 

def index(request):
    return render(request, 'index.html')

def logout(request):
    auth_logout(request)
    return redirect('index') 

@login_required
def apply_verification(request):
    """申请认证"""
    # 获取用户之前的申请记录
    previous_applications = VerificationApplication.objects.filter(
        member=request.user.member
    ).order_by('-created_at')
    
    if request.method == 'POST':
        # 检查是否有待审核的申请
        if previous_applications.filter(status='pending').exists():
            messages.error(request, '您已有一个待审核的申请，请等待审核完成后再次提交。')
            return redirect('apply_verification')
            
        # 创建申请
        application = VerificationApplication.objects.create(
            member=request.user.member,
            real_name=request.POST.get('real_name'),
            student_id=request.POST.get('student_id'),
            identity_title=request.POST.get('identity_title'),
            identity_type=request.POST.get('identity_type')
        )
        
        messages.success(request, '申请提交成功，请等待审核。')
        return redirect('apply_verification')
    
    return render(request, 'members/verify.html', {
        'previous_applications': previous_applications,
        'identity_choices': VerificationApplication.IDENTITY_CHOICES,
    }) 

@permission_required('members.can_review_applications', raise_exception=True)
def review_applications(request):
    """审核申请列表"""
    status = request.GET.get('status', 'pending')
    
    applications = VerificationApplication.objects.all().order_by('-created_at')
    if status != 'all':
        applications = applications.filter(status=status)
        
    return render(request, 'members/review.html', {
        'applications': applications,
        'status': status,
        'identity_choices': VerificationApplication.IDENTITY_CHOICES,
    })

@permission_required('members.can_review_applications', raise_exception=True)
def edit_application(request, application_id):
    """编辑申请"""
    application = get_object_or_404(VerificationApplication, id=application_id)
    
    if request.method == 'POST':
        application.real_name = request.POST.get('real_name')
        application.student_id = request.POST.get('student_id')
        application.identity_title = request.POST.get('identity_title')
        application.identity_type = request.POST.get('identity_type')
        application.save()
        
        messages.success(request, '申请信息已更新')
        return redirect('review_applications')
        
    return redirect('review_applications')

@permission_required('members.can_review_applications', raise_exception=True)
def approve_application(request, application_id):
    """通过申请"""
    if request.method == 'POST':
        application = get_object_or_404(VerificationApplication, id=application_id)
        application.status = 'approved'
        application.save()
        
        # 更新用户身份
        member = application.member
        # 根据身份类型设置等级
        identity_levels = {
            'active': 1,    # 活跃成员
            'core': 2,      # 核心成员
            'key': 3,       # 核心贡献
            'management': 4, # 管理层
            'outstanding': 5, # 卓越贡献
            'smart_car': 6 # 智能车团队
        }
        member.identity_level = identity_levels.get(application.identity_type, 0)
        member.identity_title = application.identity_title
        member.save()
        
        messages.success(request, '已通过申请')
    return redirect('review_applications')

@permission_required('members.can_review_applications', raise_exception=True)
def reject_application(request, application_id):
    """拒绝申请"""
    if request.method == 'POST':
        application = get_object_or_404(VerificationApplication, id=application_id)
        application.status = 'rejected'
        application.save()
        messages.success(request, '已拒绝申请')
    return redirect('review_applications') 

@login_required
def identity_card(request):
    """显示身份卡"""
    try:
        member = Member.objects.get(user=request.user)
        # 获取该用户所有已通过的申请
        approved_applications = VerificationApplication.objects.filter(
            member=member,
            status='approved'
        ).order_by('-updated_at')
        
        # 如果没有已通过的认证，显示默认卡片
        if not approved_applications.exists():
            cards = [{
                'image': member.get_identity_card_image(),
                'title': '未认证',
                'level': 0,
                'identity_title': '',
                'updated_at': None
            }]
        else:
            cards = []
            for app in approved_applications:
                identity_levels = {
                    'active': 1,
                    'core': 2,
                    'key': 3,
                    'management': 4,
                    'outstanding': 5,
                    'smart_car': 6
                }
                level = identity_levels.get(app.identity_type, 0)
                cards.append({
                    'image': f'https://esd-id.emoera.com/images/level_{level}.png',
                    'title': app.get_identity_type_display(),
                    'level': level,
                    'identity_title': app.identity_title,
                    'updated_at': app.updated_at
                })
        
        return render(request, 'members/identity_card.html', {
            'member': member,
            'cards': cards,
        })
    except Member.DoesNotExist:
        return redirect('login') 

def get_latest_verification(request):
    """
    获取用户最近一次认证的身份信息
    GET 参数:
        oauth_id: 用户的 OAuth ID
    返回:
        JSON 格式的认证信息，包含:
        - identity_type: 认证身份类型
        - identity_type_display: 认证身份类型显示名称
        - verified_at: 认证时间
        - status: 认证状态
    """
    oauth_id = request.GET.get('oauth_id')
    
    if not oauth_id:
        return JsonResponse({
            'error': '缺少必要参数 oauth_id'
        }, status=400, json_dumps_params={'ensure_ascii': False})
    
    # 获取用户
    member = get_object_or_404(Member, oauth_id=oauth_id)
    
    # 获取最新的认证申请
    latest_verification = VerificationApplication.objects.filter(
        member=member,
        status='approved'  # 只获取已通过的认证
    ).order_by('-created_at').first()
    
    if not latest_verification:
        return JsonResponse({
            'message': '未找到认证记录'
        }, status=404, json_dumps_params={'ensure_ascii': False})
    
    return JsonResponse({
        'identity_type': latest_verification.identity_type,
        'identity_type_display': latest_verification.get_identity_type_display(),
        'verified_at': latest_verification.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'status': latest_verification.status
    }, json_dumps_params={'ensure_ascii': False})


# ===== 社团报名相关视图 =====

@login_required
def check_external_verification(request):
    """检查外部认证状态API"""
    try:
        member = Member.objects.get(user=request.user)
        oauth_id = str(member.oauth_id)
        scheme_id = 3  # 固定为3
        
        # 调用外部API检查认证状态
        api_url = "https://trust.emoera.com/api/verification/status"
        params = {
            'oauthId': oauth_id,
            'schemeId': scheme_id
        }
        
        try:
            response = requests.get(api_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    verification_data = data.get('data', {})
                    verified = verification_data.get('verified', False)
                    status = verification_data.get('status', 'unknown')
                    
                    # 修改验证逻辑：只有状态为 'approved' 才算通过
                    is_approved = status == 'approved'
                    
                    return JsonResponse({
                        'success': True,
                        'verified': verified,
                        'status': status,
                        'is_approved': is_approved,
                        'is_not_submitted': status == 'not_submitted'
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'message': data.get('message', '认证检查失败')
                    })
            elif response.status_code == 404:
                return JsonResponse({
                    'success': False,
                    'message': '用户未在认证系统中注册 (404)，请先前往 trust.emoera.com 注册并完成认证'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': f'认证服务返回错误状态: {response.status_code}'
                })
        except requests.RequestException as e:
            return JsonResponse({
                'success': False,
                'message': f'连接认证服务失败: {str(e)}'
            })
            
    except Member.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': '用户信息不存在'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'系统错误: {str(e)}'
        })


@login_required
def club_application_page(request):
    """社团报名主页面"""
    try:
        member = Member.objects.get(user=request.user)
        
        # 检查是否已有有效申请记录（被拒绝的申请不算）
        existing_application = ClubApplication.objects.filter(member=member).exclude(status='rejected').first()
        
        # 检查是否有被拒绝的申请记录
        rejected_application = ClubApplication.objects.filter(member=member, status='rejected').order_by('-created_at').first()
        
        return render(request, 'members/club_application.html', {
            'member': member,
            'user_email': request.user.email,
            'existing_application': existing_application,
            'rejected_application': rejected_application
        })
    except Member.DoesNotExist:
        return redirect('login')


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def submit_club_application(request):
    """提交社团报名申请"""
    try:
        data = json.loads(request.body)
        real_name = data.get('real_name', '').strip()
        
        if not real_name:
            return JsonResponse({
                'success': False,
                'message': '请填写真实姓名'
            })
        
        member = Member.objects.get(user=request.user)
        
        # 检查是否已有有效申请记录（被拒绝的申请可以重新提交）
        existing_application = ClubApplication.objects.filter(member=member).exclude(status='rejected').first()
        if existing_application:
            return JsonResponse({
                'success': False,
                'message': '您已提交过申请，请等待审核'
            })
        
        # 创建申请记录
        application = ClubApplication.objects.create(
            member=member,
            real_name=real_name,
            external_verification_status=data.get('external_status', ''),
            external_verified=data.get('external_verified', False)
        )
        
        return JsonResponse({
            'success': True,
            'message': '提交成功'
        })
        
    except Member.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': '用户信息不存在'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'提交失败: {str(e)}'
        })


@login_required
def application_status_page(request):
    """申请状态页面"""
    try:
        member = Member.objects.get(user=request.user)
        application = ClubApplication.objects.filter(member=member).order_by('-created_at').first()
        
        if not application:
            return redirect('club_application')
        
        return render(request, 'members/application_status.html', {
            'application': application
        })
    except Member.DoesNotExist:
        return redirect('login')


@permission_required('members.can_review_club_applications', raise_exception=True)
def review_club_applications(request):
    """管理员审核社团申请"""
    status = request.GET.get('status', 'pending')
    
    applications = ClubApplication.objects.all().order_by('-created_at')
    # 统计各状态数量（用于前端统计卡片展示）
    total_count = applications.count()
    pending_count = applications.filter(status='pending').count()
    interview_sent_count = applications.filter(status='interview_sent').count()
    offer_sent_count = applications.filter(status='offer_sent').count()
    offer_confirmed_count = applications.filter(status='offer_confirmed').count()
    rejected_count = applications.filter(status='rejected').count()

    # 列表展示可按筛选条件过滤
    list_applications = applications
    if status != 'all':
        list_applications = applications.filter(status=status)
    
    return render(request, 'members/review_club_applications.html', {
        'applications': list_applications,
        'status': status,
        'status_choices': ClubApplication.STATUS_CHOICES,
        # 统计数据
        'total_count': total_count,
        'pending_count': pending_count,
        'interview_sent_count': interview_sent_count,
        'offer_sent_count': offer_sent_count,
        'offer_confirmed_count': offer_confirmed_count,
        'rejected_count': rejected_count,
    })


@permission_required('members.can_send_interview_notifications', raise_exception=True)
def send_interview_notification(request, application_id):
    """发送笔试通知"""
    if request.method == 'POST':
        application = get_object_or_404(ClubApplication, id=application_id)
        
        # 更新状态
        application.status = 'interview_sent'
        application.interview_sent_at = timezone.now()
        application.save()
        
        # 发送笔试通知邮件
        send_interview_email(application.member.user.email, application.real_name)
        
        messages.success(request, f'已向 {application.real_name} 发送笔试通知')
    
    return redirect('review_club_applications')


@permission_required('members.can_send_interview_notifications', raise_exception=True)
def resend_interview_notification(request, application_id):
    """重发笔试通知"""
    if request.method == 'POST':
        application = get_object_or_404(ClubApplication, id=application_id)
        
        # 验证申请状态（只有已发送笔试通知的申请才能重发）
        if application.status != 'interview_sent':
            messages.error(request, f'{application.real_name} 的申请状态不是"笔试通知已发送"，无法重发')
            return redirect('review_club_applications')
        
        # 重新发送笔试通知邮件（不改变状态和时间戳）
        success = send_interview_email(application.member.user.email, application.real_name)
        
        if success:
            messages.success(request, f'已向 {application.real_name} 重新发送笔试通知')
        else:
            messages.error(request, f'向 {application.real_name} 重发笔试通知失败，请检查邮件配置')
    
    return redirect('review_club_applications')


@permission_required('members.can_send_offer_notifications', raise_exception=True)
def send_offer_notification(request, application_id):
    """发送录取通知"""
    if request.method == 'POST':
        application = get_object_or_404(ClubApplication, id=application_id)
        
        # 更新状态
        application.status = 'offer_sent'
        application.offer_sent_at = timezone.now()
        application.save()
        
        # 发送录取通知邮件
        send_offer_email(application.member.user.email, application.real_name, str(application.offer_uuid))
        
        messages.success(request, f'已向 {application.real_name} 发送录取通知')
    
    return redirect('review_club_applications')


@permission_required('members.can_send_offer_notifications', raise_exception=True)
def resend_offer_notification(request, application_id):
    """重发录取通知"""
    if request.method == 'POST':
        application = get_object_or_404(ClubApplication, id=application_id)
        
        # 验证申请状态（只有已发送录取通知的申请才能重发）
        if application.status != 'offer_sent':
            messages.error(request, f'{application.real_name} 的申请状态不是"录取通知已发送"，无法重发')
            return redirect('review_club_applications')
        
        # 重新发送录取通知邮件（不改变状态和时间戳）
        success = send_offer_email(application.member.user.email, application.real_name, str(application.offer_uuid))
        
        if success:
            messages.success(request, f'已向 {application.real_name} 重新发送录取通知')
        else:
            messages.error(request, f'向 {application.real_name} 重发录取通知失败，请检查邮件配置')
    
    return redirect('review_club_applications')


@csrf_exempt
def confirm_offer(request, offer_uuid):
    """确认Offer页面"""
    try:
        application = ClubApplication.objects.get(offer_uuid=offer_uuid)
        
        if request.method == 'POST':
            if application.status == 'offer_sent':
                application.status = 'offer_confirmed'
                application.offer_confirmed_at = timezone.now()
                application.save()
                return JsonResponse({'status': 'success'})
            else:
                return JsonResponse({'status': 'already_confirmed'})
        
        return render(request, 'members/confirm_offer.html', {
            'application': application,
            'confirmed': application.status == 'offer_confirmed'
        })
        
    except ClubApplication.DoesNotExist:
        return render(request, 'members/confirm_offer.html', {
            'error': '无效的确认码'
        })


# ===== 邮件发送功能 =====

def send_interview_email(to_email, to_name):
    """发送笔试通知邮件"""
    try:
        subject = '欢迎您参加E时代笔试！'
        
        # HTML 邮件内容（基于提供的PHP示例）
        html_message = f'''
        <p>同学您好，<br>感谢您参与E时代的笔试。为了及时获取最新消息，请关注我们的QQ交流群。</p>
        <img src="https://eaccount.emoera.com/photos/bishitongzhi.png" alt="E时代" style="width:500px;height:auto;">
        <br><br>
        <p>E时代团队向您表达由衷的祝贺，祝您在本次笔试中取得佳绩。我们也期待更多优秀的同学与我们一起成长，共创辉煌。<br>祝顺利通过！<br>E时代研发中心</p>
        '''
        
        # 纯文本版本
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info("Interview notification email sent")
        return True
    except Exception as e:
        logger.exception("Failed to send interview notification email")
        return False


def send_offer_email(to_email, to_name, offer_uuid):
    """发送录取通知邮件"""
    confirm_url = ''
    try:
        subject = '确认您的 Offer'
        
        # 构建确认链接（使用当前域名）
        from django.urls import reverse
        from django.contrib.sites.shortcuts import get_current_site
        
        base_url = settings.OFFER_CONFIRM_BASE_URL
            
        confirm_path = reverse('confirm_offer', kwargs={'offer_uuid': offer_uuid})
        confirm_url = f"{base_url}{confirm_path}"
        
        # HTML 邮件内容（基于提供的PHP示例）
        html_message = f'''
        <p>您好， {to_name},</p>
        <p>感谢您对E时代的关注与支持！我们的社团文化是开放包容，真诚热爱，欢迎您的加入。</p>
        <p>请点击以下链接确认您的 Offer：</p>
        <a href='{confirm_url}'>确认 Offer</a>
        <br><br>
        <p>期待与您一同开启新的征程，互相支持，共同成长。</p>
        <a href='{confirm_url}'>
            <img src='https://eaccount.emoera.com/photos/welcome.png' alt='E时代' style='width: auto; height: auto;'>
        </a>
        <br><br>
        <p>再次感谢您的加入<br>E时代研发中心</p>
        '''
        
        # 纯文本版本
        plain_message = f'''您好，{to_name},

感谢您对E时代的关注与支持！我们的社团文化是开放包容，真诚热爱，欢迎您的加入。

请访问以下链接确认您的 Offer：
{confirm_url}

期待与您一同开启新的征程，互相支持，共同成长。

再次感谢您的加入
E时代研发中心'''
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info("Offer email sent")
        return True
    except Exception as e:
        logger.exception("Failed to send offer email")
        return False


@permission_required('members.can_review_club_applications', raise_exception=True)
def reject_club_application(request, application_id):
    """拒绝社团申请"""
    if request.method == 'POST':
        application = get_object_or_404(ClubApplication, id=application_id)
        application.status = 'rejected'
        application.save()
        messages.success(request, f'已拒绝 {application.real_name} 的申请')
    
    return redirect('review_club_applications') 