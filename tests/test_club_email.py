"""Mail failures must not advance applications or announce a successful send."""

from datetime import datetime, timezone
from smtplib import SMTPAuthenticationError
from unittest.mock import patch

from django.contrib.auth.models import User
from django.contrib.messages import ERROR, SUCCESS, get_messages
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from members import views
from members.models import ClubApplication, Member


@override_settings(EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend')
class ClubEmailTests(TestCase):
    def setUp(self):
        user = User.objects.create_user('applicant', email='recipient@example.invalid')
        member = Member.objects.create(user=user, oauth_id=1)
        self.application = ClubApplication.objects.create(member=member, real_name='测试申请人')
        reviewer = User.objects.create_user('reviewer', is_superuser=True)
        self.client.force_login(reviewer)
        notify = patch('members.views.notify_club_event_async')
        self.notify = notify.start()
        self.addCleanup(notify.stop)
        network = patch('requests.post', side_effect=AssertionError('Tests must not send webhooks'))
        network.start()
        self.addCleanup(network.stop)

    def messages(self, response):
        result = list(get_messages(response.wsgi_request))
        # Model the browser consuming the redirect's flash messages before the
        # next independent action in a subtest.
        self.client.cookies.pop('messages', None)
        return result

    def post(self, route):
        response = self.client.post(reverse(route, args=[self.application.id]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('review_club_applications'))
        return response

    def snapshot(self):
        self.application.refresh_from_db()
        return (self.application.status, self.application.interview_sent_at,
                self.application.offer_sent_at, self.application.updated_at)

    def test_first_sends_preserve_state_and_timestamps_on_smtp_failure(self):
        for kind in ['interview', 'offer']:
            with self.subTest(kind=kind):
                before = self.snapshot()
                with patch('members.views.send_mail', side_effect=SMTPAuthenticationError(535, b'rejected')):
                    with self.assertLogs('members.views', level='ERROR'):
                        response = self.post(f'send_{kind}_notification')
                self.assertEqual(self.snapshot(), before)
                self.notify.assert_not_called()
                messages = self.messages(response)
                self.assertEqual([message.level for message in messages], [ERROR])
                self.assertIn('申请状态未变更', str(messages[0]))

    def test_first_sends_do_not_advance_when_backend_accepts_zero_messages(self):
        for kind in ['interview', 'offer']:
            with self.subTest(kind=kind):
                before = self.snapshot()
                with patch('members.views.send_mail', return_value=0):
                    with self.assertLogs('members.views', level='ERROR'):
                        response = self.post(f'send_{kind}_notification')
                self.assertEqual(self.snapshot(), before)
                self.notify.assert_not_called()
                self.assertEqual([message.level for message in self.messages(response)], [ERROR])

    def test_first_sends_advance_only_after_backend_acceptance(self):
        for kind in ['interview', 'offer']:
            with self.subTest(kind=kind):
                self.application.status = 'pending' if kind == 'interview' else 'interview_sent'
                self.application.save()
                before = self.snapshot()

                def accepted(**kwargs):
                    self.assertEqual(self.snapshot(), before)
                    self.assertEqual(kwargs['recipient_list'], ['recipient@example.invalid'])
                    return 1

                self.notify.reset_mock()
                with patch('members.views.send_mail', side_effect=accepted):
                    response = self.post(f'send_{kind}_notification')
                self.application.refresh_from_db()
                self.assertEqual(self.application.status, f'{kind}_sent')
                self.assertIsNotNone(getattr(self.application, f'{kind}_sent_at'))
                self.notify.assert_called_once()
                self.assertEqual(self.notify.call_args.kwargs['status'], f'{kind}_sent')
                self.assertEqual([message.level for message in self.messages(response)], [SUCCESS])

    def test_resend_failure_keeps_existing_status_and_original_send_time(self):
        old = datetime(2026, 9, 1, tzinfo=timezone.utc)
        for kind in ['interview', 'offer']:
            with self.subTest(kind=kind):
                self.application.status = f'{kind}_sent'
                setattr(self.application, f'{kind}_sent_at', old)
                self.application.save()
                before = self.snapshot()
                with patch('members.views.send_mail', return_value=0):
                    with self.assertLogs('members.views', level='ERROR'):
                        response = self.post(f'resend_{kind}_notification')
                self.assertEqual(self.snapshot(), before)
                self.notify.assert_not_called()
                self.assertEqual([message.level for message in self.messages(response)], [ERROR])

    def test_missing_smtp_configuration_is_reported_without_a_network_attempt(self):
        for kind in ['interview', 'offer']:
            with self.subTest(kind=kind):
                before = self.snapshot()
                with override_settings(EMAIL_HOST='', EMAIL_HOST_USER='', EMAIL_HOST_PASSWORD=''):
                    with patch('members.views.send_mail') as send:
                        with self.assertLogs('members.views', level='ERROR') as logs:
                            response = self.post(f'send_{kind}_notification')
                send.assert_not_called()
                self.assertIn('EMAIL_HOST is required', '\n'.join(logs.output))
                self.assertEqual(self.snapshot(), before)
                self.assertEqual([message.level for message in self.messages(response)], [ERROR])

    def test_invalid_or_missing_recipient_does_not_send_or_advance(self):
        for address in ['', 'not-an-email']:
            for kind in ['interview', 'offer']:
                with self.subTest(address=address, kind=kind):
                    user = self.application.member.user
                    user.email = address
                    user.save()
                    before = self.snapshot()
                    with patch('members.views.send_mail') as send:
                        with self.assertLogs('members.views', level='ERROR'):
                            response = self.post(f'send_{kind}_notification')
                    send.assert_not_called()
                    self.assertEqual(self.snapshot(), before)
                    self.assertEqual([message.level for message in self.messages(response)], [ERROR])

    @override_settings(DEFAULT_FROM_EMAIL='')
    def test_missing_sender_is_reported_without_sending(self):
        with patch('members.views.send_mail') as send:
            with self.assertLogs('members.views', level='ERROR'):
                self.assertFalse(views.send_interview_email('recipient@example.invalid', '测试申请人'))
        send.assert_not_called()

    @override_settings(EMAIL_USE_TLS=True, EMAIL_USE_SSL=True)
    def test_incompatible_tls_settings_are_reported_without_sending(self):
        with patch('members.views.send_mail') as send:
            with self.assertLogs('members.views', level='ERROR'):
                self.assertFalse(views.send_offer_email('recipient@example.invalid', '测试申请人', self.application.offer_uuid))
        send.assert_not_called()

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend', EMAIL_HOST='')
    def test_non_smtp_backend_remains_usable_for_local_development(self):
        self.assertTrue(views.send_interview_email('recipient@example.invalid', '测试申请人'))
        self.assertTrue(views.send_offer_email('recipient@example.invalid', '测试申请人', self.application.offer_uuid))
        self.assertEqual(len(mail.outbox), 2)
        self.assertIn(str(self.application.offer_uuid), mail.outbox[1].body)

    def test_get_requests_never_send_or_advance(self):
        before = self.snapshot()
        with patch('members.views.send_mail') as send:
            for route in ['send_interview_notification', 'send_offer_notification',
                          'resend_interview_notification', 'resend_offer_notification']:
                self.assertEqual(self.client.get(reverse(route, args=[self.application.id])).status_code, 302)
        send.assert_not_called()
        self.notify.assert_not_called()
        self.assertEqual(self.snapshot(), before)

    def test_review_permissions_remain_required(self):
        self.client.force_login(User.objects.create_user('unprivileged'))
        before = self.snapshot()
        with patch('members.views.send_mail') as send:
            for route in ['send_interview_notification', 'send_offer_notification']:
                response = self.client.post(reverse(route, args=[self.application.id]))
                self.assertEqual(response.status_code, 403)
        send.assert_not_called()
        self.notify.assert_not_called()
        self.assertEqual(self.snapshot(), before)
