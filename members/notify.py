"""Group robot notifications for WeCom / Feishu.

Webhook URLs must come from environment variables — never hardcode secrets.

Supported settings / env:
  WECOM_WEBHOOK_URL
  FEISHU_WEBHOOK_URL
  NOTIFY_WEBHOOK_URLS  (comma-separated; type inferred from URL)
"""

from __future__ import annotations

import logging
from typing import Iterable
from urllib.parse import urlparse

import requests
from django.conf import settings
from django.utils import timezone

from .notification_payload import build_event_payload

logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 5


def _split_urls(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in str(value).split(',') if item.strip()]


def _detect_provider(url: str) -> str:
    host = (urlparse(url).hostname or '').lower()
    if 'qyapi.weixin.qq.com' in host or host.endswith('weixin.qq.com'):
        return 'wecom'
    if 'feishu.cn' in host or 'larksuite.com' in host:
        return 'feishu'
    return 'unknown'


def _collect_targets() -> list[dict]:
    targets: list[dict] = []
    for url in _split_urls(getattr(settings, 'WECOM_WEBHOOK_URL', '') or ''):
        targets.append({'url': url, 'provider': 'wecom'})
    for url in _split_urls(getattr(settings, 'FEISHU_WEBHOOK_URL', '') or ''):
        targets.append({'url': url, 'provider': 'feishu'})
    for url in _split_urls(getattr(settings, 'NOTIFY_WEBHOOK_URLS', '') or ''):
        targets.append({'url': url, 'provider': _detect_provider(url)})

    seen: set[str] = set()
    unique: list[dict] = []
    for target in targets:
        if target['url'] in seen:
            continue
        seen.add(target['url'])
        unique.append(target)
    return unique


def _build_payload(provider: str, text: str) -> dict:
    if provider == 'feishu':
        return {'msg_type': 'text', 'content': {'text': text}}
    return {'msgtype': 'text', 'text': {'content': text}}


def _post_webhook(target: dict, payload: dict) -> bool:
    try:
        response = requests.post(
            target['url'],
            json=payload,
            timeout=TIMEOUT_SECONDS,
            headers={'Content-Type': 'application/json'},
        )
        if not 200 <= response.status_code < 300:
            logger.error('notify %s HTTP %s', target['provider'], response.status_code)
            return False
        body = {}
        try:
            body = response.json()
        except ValueError:
            body = {}
        if not isinstance(body, dict):
            logger.error('notify %s invalid response', target['provider'])
            return False
        if isinstance(body.get('errcode'), int) and body['errcode'] != 0:
            logger.error('notify wecom errcode=%s', body.get('errcode'))
            return False
        if isinstance(body.get('code'), int) and body['code'] != 0:
            logger.error('notify feishu code=%s', body.get('code'))
            return False
        return True
    except requests.RequestException as exc:
        # Request exception text can expose the webhook secret.
        logger.error('notify %s failed: %s', target['provider'], type(exc).__name__)
        return False


def notify_text(text: str) -> list[bool]:
    """Fire-and-forget text notification. Never raises; never logs webhook URLs."""
    message = (text or '').strip()
    if not message:
        return []
    targets = _collect_targets()
    if not targets:
        return []
    return [_post_webhook(target, _build_payload(target['provider'], message)) for target in targets]


def _safe(value, fallback: str = '-') -> str:
    if value is None or value == '':
        return fallback
    return str(value)


def notify_event(title: str, lines: Iterable[str] | None = None) -> list[bool]:
    parts = [f'【{title}】']
    if lines:
        parts.extend(str(line) for line in lines if line is not None and str(line) != '')
    parts.append(f"时间: {timezone.localtime().strftime('%Y-%m-%d %H:%M:%S')}")
    return notify_text('\n'.join(parts))


def _notify_application(**event) -> list[bool]:
    return [_post_webhook(target, build_event_payload(target['provider'], **event))
            for target in _collect_targets()]


def notify_verification_event(*, event: str, application_id, username: str, identity_type: str = '', status: str = '') -> list[bool]:
    return _notify_application(kind='verification', event=event, application_id=application_id,
                               username=username, identity_type=identity_type, status=status)


def notify_club_event(*, event: str, application_id, username: str, status: str = '') -> list[bool]:
    # Omit real names, email, student identifiers and Offer confirmation tokens.
    return _notify_application(kind='club', event=event, application_id=application_id,
                               username=username, status=status)
