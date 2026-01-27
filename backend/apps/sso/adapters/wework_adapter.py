"""
WeWork Adapter

WeWork (企业微信) API adapter for SSO integration.
Handles OAuth2 flow, user info retrieval, and message sending.
"""
import requests
from typing import Optional, Dict, List
from django.core.cache import cache
from urllib.parse import quote


class WeWorkAdapter:
    """WeWork (企业微信) Adapter for SSO integration."""

    API_BASE = "https://qyapi.weixin.qq.com/cgi-bin"
    OAUTH_BASE = "https://open.weixin.qq.com/connect/oauth2"
    QR_CONNECT_BASE = "https://open.work.weixin.qq.com/wwopen/sso/qrConnect"

    def __init__(self, config):
        """Initialize adapter with WeWork configuration.

        Args:
            config: WeWorkConfig instance
        """
        self.config = config
        self.corp_id = config.corp_id
        self.agent_id = config.agent_id
        self.agent_secret = config.agent_secret

    def get_access_token(self) -> str:
        """Get access_token from WeWork API (with caching).

        Returns:
            Access token string

        Raises:
            Exception: If API call fails
        """
        cache_key = f"wework:access_token:{self.corp_id}:{self.agent_id}"
        token = cache.get(cache_key)

        if token:
            return token

        # Fetch from WeWork API
        url = f"{self.API_BASE}/gettoken"
        params = {
            "corpid": self.corp_id,
            "corpsecret": self.agent_secret
        }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data['errcode'] != 0:
            raise Exception(f"Failed to get access_token: {data['errmsg']}")

        token = data['access_token']
        # Cache token, expire 5 minutes early
        expires_in = data.get('expires_in', 7200) - 300
        cache.set(cache_key, token, expires_in)

        return token

    def get_jsapi_ticket(self) -> str:
        """Get jsapi_ticket for frontend JSAPI usage (with caching).

        Returns:
            jsapi_ticket string

        Raises:
            Exception: If API call fails
        """
        cache_key = f"wework:jsapi_ticket:{self.corp_id}:{self.agent_id}"
        ticket = cache.get(cache_key)

        if ticket:
            return ticket

        access_token = self.get_access_token()
        url = f"{self.API_BASE}/get_jsapi_ticket"
        params = {"access_token": access_token}

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data['errcode'] != 0:
            raise Exception(f"Failed to get jsapi_ticket: {data['errmsg']}")

        ticket = data['ticket']
        expires_in = data.get('expires_in', 7200) - 300
        cache.set(cache_key, ticket, expires_in)

        return ticket

    def get_oauth_url(self, redirect_uri: str, state: str = '',
                      scope: str = 'snsapi_base') -> str:
        """Get OAuth authorization URL (for in-page redirect).

        Args:
            redirect_uri: Callback URL after authorization
            state: Anti-CSRF state token
            scope: Authorization scope
                - snsapi_base: Silent auth, get member userid
                - snsapi_userinfo: Silent auth, get member detail
                - snsapi_privateinfo: Manual auth, get detail + sensitive info

        Returns:
            OAuth authorization URL
        """
        params = {
            "appid": self.corp_id,
            "redirect_uri": quote(redirect_uri),
            "response_type": "code",
            "scope": scope,
            "agentid": self.agent_id,
            "state": state
        }

        param_str = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.OAUTH_BASE}/authorize?{param_str}#wechat_redirect"

    def get_qr_connect_url(self, redirect_uri: str, state: str = '',
                           size: str = '') -> str:
        """Get QR code login URL (for PC scan login).

        Args:
            redirect_uri: Callback URL after authorization
            state: Anti-CSRF state token
            size: QR code size (430, 560)

        Returns:
            QR code login URL
        """
        params = {
            "appid": self.corp_id,
            "agentid": self.agent_id,
            "redirect_uri": quote(redirect_uri),
            "state": state,
            "usertype": "member"
        }

        if size:
            params["size"] = size

        param_str = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.QR_CONNECT_BASE}?{param_str}"

    def get_user_info_by_code(self, code: str) -> Dict:
        """Get user info by OAuth authorization code.

        Args:
            code: OAuth authorization code

        Returns:
            User info dictionary

        Raises:
            Exception: If API call fails
        """
        # 1. Get user userid
        access_token = self.get_access_token()
        url = f"{self.API_BASE}/auth/getuserinfo"
        params = {
            "access_token": access_token,
            "code": code
        }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data['errcode'] != 0:
            raise Exception(f"Failed to get user userid: {data['errmsg']}")

        user_id = data['userid']

        # 2. Get user detail
        return self.get_user_detail(user_id)

    def get_user_detail(self, user_id: str) -> Dict:
        """Get user detail information.

        Args:
            user_id: WeWork userid

        Returns:
            User detail dictionary

        Raises:
            Exception: If API call fails
        """
        access_token = self.get_access_token()
        url = f"{self.API_BASE}/user/get"
        params = {
            "access_token": access_token,
            "userid": user_id
        }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data['errcode'] != 0:
            raise Exception(f"Failed to get user detail: {data['errmsg']}")

        return {
            'userid': data['userid'],
            'name': data['name'],
            'english_name': data.get('english_name', ''),
            'department': data.get('department', []),
            'order_in_depts': data.get('order_in_depts', []),
            'position': data.get('position', ''),
            'mobile': data.get('mobile', ''),
            'gender': data.get('gender', ''),
            'email': data.get('email', ''),
            'avatar': data.get('avatar', ''),
            'status': data.get('status', 1),
            'is_leader': data.get('isleader', 0),
            'direct_leader': data.get('direct_leader', []),
            'main_department': data.get('main_department', 0),
        }

    def get_department_list(self) -> List[Dict]:
        """Get department list.

        Returns:
            List of department dictionaries

        Raises:
            Exception: If API call fails
        """
        access_token = self.get_access_token()
        url = f"{self.API_BASE}/department/list"
        params = {"access_token": access_token}

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data['errcode'] != 0:
            raise Exception(f"Failed to get department list: {data['errmsg']}")

        return data.get('department', [])

    def get_user_list(self, department_id: int = None,
                      fetch_child: bool = False) -> List[Dict]:
        """Get department member list.

        Args:
            department_id: Department ID, None for all
            fetch_child: Whether to recursively get child department members

        Returns:
            List of user dictionaries

        Raises:
            Exception: If API call fails
        """
        access_token = self.get_access_token()
        url = f"{self.API_BASE}/user/list"
        params = {
            "access_token": access_token,
            "department_id": department_id,
            "fetch_child": 1 if fetch_child else 0
        }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data['errcode'] != 0:
            raise Exception(f"Failed to get user list: {data['errmsg']}")

        return data.get('userlist', [])

    def send_message(self, user_id: str, content: str,
                    msg_type: str = 'text') -> Dict:
        """Send application message.

        Args:
            user_id: Recipient userid
            content: Message content
            msg_type: Message type (text/image/file/textcard/news)

        Returns:
            Response dictionary

        Raises:
            Exception: If API call fails
        """
        access_token = self.get_access_token()
        url = f"{self.API_BASE}/message/send"
        params = {"access_token": access_token}

        if msg_type == 'text':
            data = {
                "touser": user_id,
                "msgtype": "text",
                "agentid": self.agent_id,
                "text": {
                    "content": content
                },
                "safe": 0
            }
        elif msg_type == 'textcard':
            data = {
                "touser": user_id,
                "msgtype": "textcard",
                "agentid": self.agent_id,
                "textcard": content
            }
        elif msg_type == 'news':
            data = {
                "touser": user_id,
                "msgtype": "news",
                "agentid": self.agent_id,
                "news": content
            }
        else:
            raise ValueError(f"Unsupported message type: {msg_type}")

        response = requests.post(url, params=params, json=data, timeout=10)
        result = response.json()

        if result['errcode'] != 0:
            raise Exception(f"Failed to send message: {result['errmsg']}")

        return result

    def get_department_users(self, department_id: int,
                             fetch_child: bool = False) -> List[Dict]:
        """Get department members (alias for get_user_list).

        Args:
            department_id: Department ID
            fetch_child: Whether to recursively get child department members

        Returns:
            List of user dictionaries

        Raises:
            Exception: If API call fails
        """
        return self.get_user_list(department_id, fetch_child)

    def get_user_info(self, user_id: str) -> Dict:
        """Get user detail by userid (alias for get_user_detail).

        Args:
            user_id: WeWork userid

        Returns:
            User detail dictionary

        Raises:
            Exception: If API call fails
        """
        return self.get_user_detail(user_id)

    def batch_get_user_info(self, user_ids: List[str]) -> List[Dict]:
        """Batch get user detail information.

        Args:
            user_ids: List of user IDs, max 100

        Returns:
            List of user detail dictionaries

        Raises:
            ValueError: If more than 100 user IDs
            Exception: If API call fails
        """
        if len(user_ids) > 100:
            raise ValueError("Maximum 100 user IDs per batch request")

        access_token = self.get_access_token()
        url = f"{self.API_BASE}/user/batchget"
        params = {"access_token": access_token}

        payload = {
            "useridlist": user_ids
        }

        response = requests.post(url, params=params, json=payload, timeout=10)
        data = response.json()

        if data['errcode'] != 0:
            raise Exception(f"Failed to batch get user info: {data['errmsg']}")

        return data.get('userlist', [])

    def get_department_id_by_name(self, name: str,
                                   parent_id: int = None) -> Optional[int]:
        """Get department ID by name (fuzzy match).

        Args:
            name: Department name to search
            parent_id: Parent department ID to narrow search

        Returns:
            Department ID if found, None otherwise

        Raises:
            Exception: If API call fails
        """
        departments = self.get_department_list()

        for dept in departments:
            # Filter by parent if specified
            if parent_id is not None and dept.get('parentid') != parent_id:
                continue

            # Fuzzy match name
            if name in dept['name']:
                return dept['id']

        return None
