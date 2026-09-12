"""OIDC / OAuth 2.0 登录模块。

实现 2026-08-27 起的新接入方案（E时代通行证）：
- Authorization Code Flow
- S256 PKCE
- RS256 ID Token（通过 JWKS 验签）
- UserInfo sub 与 ID Token sub 一致性校验

参考端点（来自 OIDC Discovery）：
- authorization_endpoint: https://account.emoera.com/api/oauth2/authorize
- token_endpoint:         https://accountapi.emoera.com/api/oidc/token
- userinfo_endpoint:      https://accountapi.emoera.com/api/oidc/userinfo
- jwks_uri:               https://accountapi.emoera.com/api/oidc/jwks
- issuer:                 https://accountapi.emoera.com/api
"""

import base64
import hashlib
import json
import logging
import secrets
import time
from urllib.parse import urlencode

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class OIDCError(Exception):
    """OIDC 登录过程中的可预期错误，视图层据此给用户友好提示。"""


def _base64url_encode(data: bytes) -> str:
    """RFC 4648 §5 的 base64url 编码（去掉 padding）。"""
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')


def generate_pkce() -> tuple[str, str]:
    """生成 (code_verifier, code_challenge)。

    code_verifier：43~128 个 RFC 7636 允许的随机字符。
    code_challenge：BASE64URL(SHA256(code_verifier))，即 S256 方法。
    """
    # token_urlsafe(64) 生成约 86 个 URL-safe 字符，落在 43~128 区间内
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode('ascii')).digest()
    challenge = _base64url_encode(digest)
    return verifier, challenge


def build_authorization_url(state: str, nonce: str, code_challenge: str) -> str:
    """构建授权端点 URL（浏览器跳转）。"""
    params = {
        'response_type': 'code',
        'client_id': settings.OIDC_CLIENT_ID,
        'redirect_uri': settings.OAUTH_CALLBACK_URL,
        'scope': settings.OIDC_SCOPES,
        'state': state,
        'nonce': nonce,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256',
    }
    return f"{settings.OIDC_AUTHORIZATION_ENDPOINT}?{urlencode(params)}"


def exchange_code(code: str, code_verifier: str) -> dict:
    """用授权码 + code_verifier 交换 access_token / id_token 等。

    Client Secret 通过 client_secret_post 方式放在表单体里（绝不出现在 URL）。
    """
    payload = {
        'grant_type': 'authorization_code',
        'client_id': settings.OIDC_CLIENT_ID,
        'client_secret': settings.OIDC_CLIENT_SECRET,
        'code': code,
        'redirect_uri': settings.OAUTH_CALLBACK_URL,
        'code_verifier': code_verifier,
    }
    try:
        resp = requests.post(settings.OIDC_TOKEN_ENDPOINT, data=payload, timeout=15)
    except requests.RequestException as e:
        raise OIDCError(f'无法连接 Token 端点：{e}') from e

    if resp.status_code != 200:
        raise OIDCError(f'Token 交换失败（HTTP {resp.status_code}）')

    try:
        data = resp.json()
    except ValueError as e:
        raise OIDCError('Token 端点返回了非 JSON 响应') from e

    if 'error' in data:
        raise OIDCError(
            f"Token 交换被拒绝：{data.get('error_description', data.get('error'))}"
        )

    return data


def fetch_jwks() -> dict:
    """获取 JWKS 公钥集合，用于 RS256 验签。"""
    try:
        resp = requests.get(settings.OIDC_JWKS_URI, timeout=15)
    except requests.RequestException as e:
        raise OIDCError(f'无法获取 JWKS：{e}') from e
    if resp.status_code != 200:
        raise OIDCError(f'获取 JWKS 失败（HTTP {resp.status_code}）')
    try:
        return resp.json()
    except ValueError as e:
        raise OIDCError('JWKS 返回了非 JSON 响应') from e


def _load_jwks_set(jwks_dict: dict):
    """把 JWKS dict 转成 jwcrypto 的 JWKSet（延迟导入 jwcrypto）。"""
    from jwcrypto import jwk

    return jwk.JWKSet.from_json(json.dumps(jwks_dict))


def _select_key(jwks_set, kid: str):
    """在 JWKSet 中按 kid 选择公钥；找不到返回 None。"""
    try:
        return jwks_set.get_key(kid=kid)
    except Exception:
        return None


def verify_id_token(id_token: str, nonce: str) -> dict:
    """验证 RS256 ID Token 并返回 claims。

    校验项（依据接入文档「四、验证 ID Token」）：
    - 签名算法必须为 RS256，不接受 Header 自报的其他算法
    - 按 header 的 kid 在 JWKS 中精确选择 RSA 公钥，验证签名
    - iss == settings.OIDC_ISSUER
    - aud 包含 settings.OIDC_CLIENT_ID
    - exp 未过期（库校验）；iat 不允许未来时间戳
    - nonce 与本次登录保存值一致
    """
    from jwcrypto import jwt
    from jwcrypto.common import json_decode

    try:
        token = jwt.JWT(jwt=id_token)
        # deserialize 后 header 不能直接读，需从底层 JWS 对象读取（返回 dict）
        header = token.token.jose_header
    except Exception as e:
        raise OIDCError(f'ID Token 无法解析：{e}') from e

    alg = header.get('alg')
    if alg != 'RS256':
        raise OIDCError(f'不支持的签名算法：{alg}')

    kid = header.get('kid')
    key = None
    for attempt in range(2):  # 最多拉取两次 JWKS，应对密钥轮换
        try:
            jwks_set = _load_jwks_set(fetch_jwks())
        except OIDCError:
            raise
        except Exception as e:
            raise OIDCError(f'JWKS 解析失败：{e}') from e

        key = _select_key(jwks_set, kid) if kid else None
        if key is not None:
            break
        if attempt == 0:
            logger.warning('ID Token kid=%s 未命中，重新拉取 JWKS', kid)

    if key is None:
        raise OIDCError(f'JWKS 中找不到 kid={kid} 的公钥')

    try:
        token.validate(key)
    except Exception as e:
        raise OIDCError(f'ID Token 签名或有效期校验失败：{e}') from e

    try:
        claims = json_decode(token.claims)
    except Exception as e:
        raise OIDCError(f'ID Token claims 解析失败：{e}') from e

    if claims.get('iss') != settings.OIDC_ISSUER:
        raise OIDCError('ID Token issuer 不匹配')

    aud = claims.get('aud')
    aud_list = aud if isinstance(aud, list) else [aud]
    if settings.OIDC_CLIENT_ID not in aud_list:
        raise OIDCError('ID Token audience 不包含当前客户端')

    if claims.get('nonce') != nonce:
        raise OIDCError('ID Token nonce 不匹配')

    iat = claims.get('iat')
    if isinstance(iat, (int, float)) and iat > int(time.time()) + 300:
        # 允许 5 分钟时钟偏移
        raise OIDCError('ID Token iat 时间戳异常（未来时间）')

    return claims


def get_userinfo(access_token: str) -> dict:
    """用 Access Token（Bearer）获取 UserInfo。"""
    try:
        resp = requests.get(
            settings.OIDC_USERINFO_ENDPOINT,
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=15,
        )
    except requests.RequestException as e:
        raise OIDCError(f'无法连接 UserInfo 端点：{e}') from e
    if resp.status_code != 200:
        raise OIDCError(f'获取 UserInfo 失败（HTTP {resp.status_code}）')
    try:
        data = resp.json()
    except ValueError as e:
        raise OIDCError('UserInfo 返回了非 JSON 响应') from e

    # 兼容历史接口返回 {code, data: {...}} 的包装格式
    if isinstance(data, dict) and isinstance(data.get('data'), dict):
        data = data['data']
    return data


def normalize_userinfo(userinfo: dict) -> dict:
    """把 UserInfo 的 claims 规范化为 create_or_update_user 需要的字段。

    OIDC 标准字段优先，兼容历史 /api/oauth2/userinfo 的字段名。
    """
    sub = userinfo.get('sub') or userinfo.get('id')
    if not sub:
        raise OIDCError('UserInfo 缺少 sub')

    return {
        'id': sub,
        'username': (
            userinfo.get('preferred_username')
            or userinfo.get('username')
            or userinfo.get('name')
            or sub
        ),
        'email': userinfo.get('email') or userinfo.get('mail') or '',
        'avatar': userinfo.get('picture') or userinfo.get('avatar') or '',
        'bio': userinfo.get('bio') or '',
    }
