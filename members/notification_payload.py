"""Pure payload construction for EID group notifications; never sends messages."""
import html
import os
import re
from urllib.parse import urlparse, urlencode
from zoneinfo import ZoneInfo

from django.conf import settings
from django.utils import timezone

STATUS = {
    'pending': '待审核', 'approved': '已通过', 'rejected': '已拒绝',
    'interview_sent': '笔试通知已发送', 'offer_sent': '录取通知已发送',
    'offer_confirmed': 'Offer 已确认',
}


def option(name, default):
    return getattr(settings, name, os.getenv(name, default)) or default


def short(value, limit=80):
    text = re.sub(r'[\r\n\t]+', ' ', str(value if value is not None else '-')).strip() or '-'
    return text if len(text) <= limit else text[:limit - 1] + '…'


def escape_markdown(value):
    return re.sub(r'([\\`*_{}\[\]()#!|])', r'\\\1', html.escape(value, quote=False))


def public_origin():
    try:
        u = urlparse(option('NOTIFY_PUBLIC_BASE_URL', 'https://neweid.emoera.com'))
        if u.scheme not in ('https', 'http') or not u.hostname or u.username or u.password:
            raise ValueError('Invalid public origin')
        return f'{u.scheme}://{u.netloc}'
    except (ValueError, TypeError):
        return 'https://neweid.emoera.com'


def build_event_payload(provider, *, kind, event, application_id, username,
                        identity_type='', status='', now=None):
    origin = public_origin()
    title = short(event, 26)
    label = STATUS.get(status, short(status or '状态更新', 20))
    fields = [('申请类型', '身份认证' if kind == 'verification' else '社团报名'),
              ('申请编号', short(application_id)), ('申请人', short(username)),
              ('当前状态', label)]
    if kind == 'verification' and identity_type:
        fields.append(('身份类型', short(identity_type)))
    # Read-only review pages; never link directly to approval or Offer actions.
    path = '/verify/review/' if kind == 'verification' else '/club/admin/'
    url = origin + path + '?' + urlencode({'status': status if status in STATUS else 'all'})
    action = '前往审核' if status == 'pending' else '查看记录'
    stamp = (now or timezone.now()).astimezone(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
    time_text = f'时间：{stamp}（北京时间）'
    text = '\n'.join(['【E时代 ID】', title, *[f'{k}：{v}' for k, v in fields], time_text, f'{action}：{url}'])
    if provider == 'wecom':
        format_name = option('WECOM_NOTIFY_FORMAT', 'card')
        if format_name == 'text':
            return {'msgtype': 'text', 'text': {'content': text}}
        if format_name == 'markdown':
            content = '\n'.join([f'### E时代 ID · {escape_markdown(title)}',
                                 *[f'> **{k}**：{escape_markdown(v)}' for k, v in fields],
                                 f'> {time_text}', f'[{action}]({url})'])
            return {'msgtype': 'markdown', 'markdown': {'content': content}}
        return {'msgtype': 'template_card', 'template_card': {
            'card_type': 'text_notice',
            'source': {'icon_url': origin + '/static/images/e-era-logo.png', 'desc': 'E时代 ID', 'desc_color': 1},
            'main_title': {'title': title, 'desc': label},
            'sub_title_text': time_text,
            'horizontal_content_list': [{'keyname': k, 'value': short(v, 26)} for k, v in fields],
            'jump_list': [{'type': 1, 'title': action, 'url': url}],
            'card_action': {'type': 1, 'url': url},
        }}
    if provider == 'feishu':
        if option('FEISHU_NOTIFY_FORMAT', 'card') == 'text':
            return {'msg_type': 'text', 'content': {'text': text}}
        color = 'green' if status in ('approved', 'offer_sent', 'offer_confirmed') else 'red' if status == 'rejected' else 'blue'
        return {'msg_type': 'interactive', 'card': {
            'config': {'wide_screen_mode': True},
            'header': {'template': color, 'title': {'tag': 'plain_text', 'content': f'E时代 ID · {title}'}},
            'elements': [
                {'tag': 'div', 'fields': [{'is_short': True, 'text': {'tag': 'plain_text', 'content': f'{k}\n{v}'}} for k, v in fields]},
                {'tag': 'note', 'elements': [{'tag': 'plain_text', 'content': time_text}]},
                {'tag': 'action', 'actions': [{'tag': 'button', 'text': {'tag': 'plain_text', 'content': action}, 'type': 'primary', 'url': url}]},
            ],
        }}
    return {'msgtype': 'text', 'text': {'content': text}}
