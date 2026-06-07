"""
URL configuration for eidProject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from members import views

urlpatterns = [
    path('', views.index, name='index'),
    path('admin/', admin.site.urls),
    path('oauth/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    path('login/', views.oauth_login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('oauth/callback/', views.oauth_callback, name='oauth_callback'),
    path('profile/', views.member_profile, name='member_profile'),
    path('api/save-token/', views.save_token, name='save_token'),
    path('verify/', views.apply_verification, name='apply_verification'),
    path('verify/review/', views.review_applications, name='review_applications'),
    path('verify/edit/<int:application_id>/', views.edit_application, name='edit_application'),
    path('verify/approve/<int:application_id>/', views.approve_application, name='approve_application'),
    path('verify/reject/<int:application_id>/', views.reject_application, name='reject_application'),
    path('identity-card/', views.identity_card, name='identity_card'),
    path('api/latest-verification/', views.get_latest_verification, name='get_latest_verification'),
    
    # 社团报名相关路由
    path('club/', views.club_application_page, name='club_application'),
    path('club/check-verification/', views.check_external_verification, name='check_external_verification'),
    path('club/submit/', views.submit_club_application, name='submit_club_application'),
    path('club/status/', views.application_status_page, name='application_status'),
    path('club/admin/', views.review_club_applications, name='review_club_applications'),
    path('club/admin/interview/<int:application_id>/', views.send_interview_notification, name='send_interview_notification'),
    path('club/admin/resend-interview/<int:application_id>/', views.resend_interview_notification, name='resend_interview_notification'),
    path('club/admin/offer/<int:application_id>/', views.send_offer_notification, name='send_offer_notification'),
    path('club/admin/resend-offer/<int:application_id>/', views.resend_offer_notification, name='resend_offer_notification'),
    path('club/admin/reject/<int:application_id>/', views.reject_club_application, name='reject_club_application'),
    path('club/confirm-offer/<uuid:offer_uuid>/', views.confirm_offer, name='confirm_offer'),
]
