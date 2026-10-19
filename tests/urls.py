from django.urls import path

from members import views

urlpatterns = [
    path('club/', views.club_application_page, name='club_application'),
    path('club/admin/', views.review_club_applications, name='review_club_applications'),
    path('club/admin/interview/<int:application_id>/', views.send_interview_notification,
         name='send_interview_notification'),
    path('club/admin/offer/<int:application_id>/', views.send_offer_notification,
         name='send_offer_notification'),
    path('club/admin/resend-interview/<int:application_id>/', views.resend_interview_notification,
         name='resend_interview_notification'),
    path('club/admin/resend-offer/<int:application_id>/', views.resend_offer_notification,
         name='resend_offer_notification'),
    path('club/confirm-offer/<uuid:offer_uuid>/', views.confirm_offer, name='confirm_offer'),
]

