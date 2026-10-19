"""Offer confirmation is read-only after acceptance, including stale requests."""

import uuid
from datetime import datetime, timezone
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from members.models import ClubApplication, Member


class OfferConfirmationTests(TestCase):
    def setUp(self):
        user = User.objects.create_user('applicant', email='recipient@example.invalid')
        member = Member.objects.create(user=user, oauth_id=1)
        self.application = ClubApplication.objects.create(
            member=member, real_name='测试申请人', status='offer_sent',
        )
        self.url = reverse('confirm_offer', args=[self.application.offer_uuid])
        notify = patch('members.views.notify_club_event_async')
        self.notify = notify.start()
        self.addCleanup(notify.stop)

    def snapshot(self):
        self.application.refresh_from_db()
        return (self.application.status, self.application.offer_confirmed_at,
                self.application.updated_at)

    def test_get_pending_offer_only_displays_acceptance_button(self):
        before = self.snapshot()
        response = self.client.get(self.url)
        self.assertContains(response, 'id="offerBtn"')
        self.assertEqual(self.snapshot(), before)
        self.notify.assert_not_called()

    def test_confirmed_page_displays_result_without_submit_button(self):
        self.application.status = 'offer_confirmed'
        self.application.offer_confirmed_at = datetime(2026, 10, 1, tzinfo=timezone.utc)
        self.application.save()
        before = self.snapshot()
        response = self.client.get(self.url)
        self.assertContains(response, 'disabled id="acceptedBtn"')
        self.assertContains(response, '确认时间：2026年10月01日')
        self.assertNotContains(response, 'id="offerBtn"')
        self.assertIn('no-store', response['Cache-Control'])
        self.assertEqual(self.snapshot(), before)
        self.notify.assert_not_called()

    def test_repeat_posts_preserve_first_confirmation_and_notify_once(self):
        first = self.client.post(self.url)
        self.assertEqual(first.json(), {'status': 'success'})
        before = self.snapshot()
        self.assertEqual(before[0], 'offer_confirmed')
        self.assertIsNotNone(before[1])
        second = self.client.post(self.url)
        self.assertEqual(second.json(), {'status': 'already_confirmed'})
        self.assertEqual(self.snapshot(), before)
        self.notify.assert_called_once()

    def test_stale_request_cannot_replace_another_requests_confirmation(self):
        stale = ClubApplication.objects.get(pk=self.application.pk)
        earlier = datetime(2026, 10, 1, tzinfo=timezone.utc)

        def read_then_rival_confirms(**kwargs):
            ClubApplication.objects.filter(pk=stale.pk).update(
                status='offer_confirmed', offer_confirmed_at=earlier, updated_at=earlier,
            )
            return stale

        with patch('members.views.ClubApplication.objects.get', side_effect=read_then_rival_confirms):
            response = self.client.post(self.url)
        self.assertEqual(response.json(), {'status': 'already_confirmed'})
        self.assertEqual(self.snapshot(), ('offer_confirmed', earlier, earlier))
        self.notify.assert_not_called()

    def test_unissued_or_rejected_offers_cannot_be_accepted(self):
        for status in ['pending', 'interview_sent', 'rejected']:
            with self.subTest(status=status):
                self.application.status = status
                self.application.save()
                before = self.snapshot()
                response = self.client.get(self.url)
                self.assertContains(response, '当前申请尚无可确认的录取通知', status_code=409)
                self.assertNotContains(response, 'id="offerBtn"', status_code=409)
                response = self.client.post(self.url)
                self.assertEqual(response.status_code, 409)
                self.assertEqual(response.json(), {'status': 'not_available'})
                self.assertEqual(self.snapshot(), before)
        self.notify.assert_not_called()

    def test_invalid_link_does_not_offer_acceptance(self):
        response = self.client.get(reverse('confirm_offer', args=[uuid.uuid4()]))
        self.assertContains(response, '无效的确认码')
        self.assertNotContains(response, 'id="offerBtn"')
        self.notify.assert_not_called()

    def test_other_methods_cannot_confirm(self):
        before = self.snapshot()
        self.assertEqual(self.client.put(self.url).status_code, 405)
        self.assertEqual(self.snapshot(), before)
        self.notify.assert_not_called()
