import json
import unittest
from datetime import datetime, timezone
from unittest.mock import Mock, patch
from urllib.parse import urlparse, parse_qs

from django.conf import settings
if not settings.configured:
    settings.configure(USE_TZ=True, TIME_ZONE='Asia/Shanghai', INSTALLED_APPS=[])
from django.test import override_settings
import requests
from members.notification_payload import build_event_payload
from members.notify import notify_club_event, notify_verification_event, notify_text


class NotificationTests(unittest.TestCase):
    def setUp(self):
        config = override_settings(WECOM_WEBHOOK_URL='', FEISHU_WEBHOOK_URL='', NOTIFY_WEBHOOK_URLS='',
                                   WECOM_NOTIFY_FORMAT='card', FEISHU_NOTIFY_FORMAT='card',
                                   NOTIFY_PUBLIC_BASE_URL='https://neweid.emoera.com')
        config.enable()
        self.addCleanup(config.disable)
        # All notification calls must remain offline, even if local env contains real credentials.
        patcher = patch('members.notify.requests.post', return_value=Mock(status_code=200, json=lambda: {'errcode': 0, 'code': 0}))
        self.post = patcher.start()
        self.addCleanup(patcher.stop)

    def payload(self, provider='wecom', **changes):
        data = dict(kind='verification', event='新身份认证申请', application_id=41, username='测试用户',
                    identity_type='核心成员', status='pending', now=datetime(2026, 9, 10, tzinfo=timezone.utc))
        data.update(changes)
        return build_event_payload(provider, **data)

    def test_all_states_and_separate_read_only_review_routes(self):
        states = {'verification': ['pending', 'approved', 'rejected'],
                  'club': ['pending', 'interview_sent', 'offer_sent', 'offer_confirmed', 'rejected']}
        for kind, statuses in states.items():
            for status in statuses:
                with self.subTest(kind=kind, status=status):
                    card = self.payload(kind=kind, status=status)['template_card']
                    parsed = urlparse(card['card_action']['url'])
                    self.assertEqual(parsed.netloc, 'neweid.emoera.com')
                    self.assertEqual(parsed.path, '/verify/review/' if kind == 'verification' else '/club/admin/')
                    self.assertEqual(parse_qs(parsed.query)['status'], [status])
                    self.assertIn('08:00:00', card['sub_title_text'])
                    self.assertEqual(card['card_type'], 'text_notice')
                    self.assertLessEqual(len(card['horizontal_content_list']), 6)
                    self.assertTrue(card['source']['icon_url'].endswith('/static/images/e-era-logo.png'))

    def test_feishu_uses_plain_text_and_status_colors(self):
        for status, color in [('pending','blue'), ('rejected','red'), ('approved','green'), ('offer_confirmed','green')]:
            card = self.payload(provider='feishu', status=status, username='<at id=all></at>')['card']
            self.assertEqual(card['header']['template'], color)
            self.assertTrue(all(f['text']['tag'] == 'plain_text' for f in card['elements'][0]['fields']))
            self.assertEqual(card['elements'][-1]['actions'][0]['tag'], 'button')

    @override_settings(WECOM_NOTIFY_FORMAT='markdown')
    def test_markdown_escapes_mentions_and_links(self):
        content = self.payload(username='<@all> [欺骗](https://evil.example)')['markdown']['content']
        self.assertNotIn('<@all>', content)
        self.assertNotIn('[欺骗](https://evil.example)', content)
        self.assertIn('前往审核', content)
        self.assertLess(len(content.encode()), 4096)

    @override_settings(WECOM_NOTIFY_FORMAT='text', FEISHU_NOTIFY_FORMAT='text')
    def test_text_configuration(self):
        self.assertEqual(self.payload()['msgtype'], 'text')
        self.assertEqual(self.payload(provider='feishu')['msg_type'], 'text')

    @override_settings(NOTIFY_PUBLIC_BASE_URL='javascript:alert(1)')
    def test_safe_origin_and_bounded_fields(self):
        card = self.payload(username='长'*5000, identity_type='长'*5000)['template_card']
        self.assertTrue(card['card_action']['url'].startswith('https://neweid.emoera.com/'))
        self.assertTrue(all(len(f['value']) <= 26 for f in card['horizontal_content_list']))
        self.assertLess(len(json.dumps(card, ensure_ascii=False).encode()), 4096)

    @override_settings(WECOM_WEBHOOK_URL='https://qyapi.weixin.qq.com/test-placeholder',
                       NOTIFY_WEBHOOK_URLS='https://qyapi.weixin.qq.com/test-placeholder',
                       FEISHU_WEBHOOK_URL='https://open.feishu.cn/test-placeholder')
    def test_lifecycle_dispatch_and_deduplication(self):
        for send in [notify_club_event, notify_verification_event]:
            self.post.reset_mock()
            self.assertEqual(send(event='测试', application_id=1, username='测试用户', status='pending'), [True, True])
            self.assertEqual(self.post.call_count, 2)
            self.assertEqual(self.post.call_args_list[0].kwargs['json']['msgtype'], 'template_card')
            self.assertEqual(self.post.call_args_list[1].kwargs['json']['msg_type'], 'interactive')
        self.post.reset_mock()
        notify_text('通用通知')
        self.assertEqual(self.post.call_args_list[0].kwargs['json']['msgtype'], 'text')

    def test_unconfigured_does_not_send(self):
        self.assertEqual(notify_club_event(event='测试', application_id=1, username='用户'), [])
        self.post.assert_not_called()

    @override_settings(WECOM_WEBHOOK_URL='https://qyapi.weixin.qq.com/secret-placeholder')
    def test_timeout_rejection_and_redacted_logs(self):
        self.post.side_effect = requests.Timeout('https://qyapi.weixin.qq.com/secret-placeholder')
        with self.assertLogs('members.notify', level='ERROR') as logs:
            result = notify_club_event(event='测试', application_id=1, username='用户')
        self.assertEqual(result, [False])
        self.assertEqual(self.post.call_count, 1)
        self.assertNotIn('secret-placeholder', str(logs.output))
        self.post.side_effect = None
        self.post.return_value = Mock(status_code=200, json=lambda: {'errcode': 40058})
        with self.assertLogs('members.notify', level='ERROR'):
            self.assertEqual(notify_club_event(event='测试', application_id=1, username='用户'), [False])


if __name__ == '__main__':
    unittest.main()
