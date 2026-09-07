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


def _post_webhook(target: dict, text: str) -> bool:
    payload = _build_payload(target['provider'], text)
    try:
        response = requests.post(
            target['url'],
            json=payload,
            timeout=TIMEOUT_SECONDS,
            headers={'Content-Type': 'application/json'},
        )
        if response.status_code >= 400:
            logger.error('notify %s HTTP %s', target['provider'], response.status_code)
            return False
        body = {}
        try:
            body = response.json()
        except ValueError:
            body = {}
        if isinstance(body.get('errcode'), int) and body['errcode'] != 0:
            logger.error('notify wecom errcode=%s', body.get('errcode'))
            return False
        if isinstance(body.get('code'), int) and body['code'] != 0:
            logger.error('notify feishu code=%s', body.get('code'))
            return False
        return True
    except requests.RequestException as exc:
        logger.error('notify %s failed: %s', target['provider'], exc)
        return False


def notify_text(text: str) -> list[bool]:
    """Fire-and-forget text notification. Never raises; never logs webhook URLs."""
    message = (text or '').strip()
    if not message:
        return []
    targets = _collect_targets()
    if not targets:
        return []
    return [_post_webhook(target, message) for target in targets]


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


def notify_verification_event(*, event: str, application_id, username: str, identity_type: str = '', status: str = '') -> list[bool]:
    return notify_event(
        'E时代会员中心',
        [
            f'事件: {_safe(event)}',
            f'类型: 身份认证',
            f'申请ID: {_safe(application_id)}',
            f'用户: {_safe(username)}',
            f'身份类型: {_safe(identity_type)}' if identity_type else '',
            f'状态: {_safe(status)}' if status else '',
        ],
    )


def notify_club_event(*, event: str, application_id, username: str, status: str = '') -> list[bool]:
    # Intentionally omit real_name / email / student identifiers.
    return notify_event(
        'E时代会员中心',
        [
            f'事件: {_safe(event)}',
            f'类型: 社团报名',
            f'申请ID: {_safe(application_id)}',
            f'用户: {_safe(username)}',
            f'状态: {_safe(status)}' if status else '',
        ],
    )
