import uuid

import httpx
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential_jitter,
)


def _should_retry(exc):
    if isinstance(exc, httpx.TransportError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code == 429 or exc.response.status_code >= 500
    return isinstance(exc, ValueError)


class FeishuRequest:
    BASE_URL = "https://open.feishu.cn"
    TIMEOUT = httpx.Timeout(20, connect=5)

    def __init__(self, app_id: str, app_secret: str):
        if not app_id or not app_secret:
            raise ValueError("missing feishu app_id or app_secret")
        self.app_id = app_id
        self.app_secret = app_secret
        self._token = None

    @property
    def tenant_access_token(self):
        if not self._token:
            self._token = self.get_tenant_access_token(self.app_id, self.app_secret)[
                "tenant_access_token"
            ]
        return self._token

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential_jitter(initial=1, max=4),
        retry=retry_if_exception(_should_retry),
        reraise=True,
    )
    def _send_request(
        self,
        url: str,
        method: str = "POST",
        require_token: bool = True,
        payload: dict = None,
        params: dict = None,
    ):
        headers = {"Content-Type": "application/json"}
        if require_token:
            headers["Authorization"] = f"Bearer {self.tenant_access_token}"

        response = httpx.request(
            method,
            url,
            headers=headers,
            json=payload,
            params=params,
            timeout=self.TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        if data.get("code") != 0:
            raise RuntimeError(
                f"feishu api error: {data.get('code')} {data.get('msg')}"
            )
        return data

    def get_tenant_access_token(self, app_id: str, app_secret: str) -> dict:
        url = f"{self.BASE_URL}/open-apis/auth/v3/tenant_access_token/internal"
        return self._send_request(
            url,
            require_token=False,
            payload={"app_id": app_id, "app_secret": app_secret},
        )

    def send_bot_message(
        self,
        content: str,
        receive_id_type: str = "open_id",
        receive_id: str = "ou_6a4cf25f0ef63a18f8979e4813d98ddc",
        msg_type: str = "interactive",
    ) -> dict:
        url = f"{self.BASE_URL}/open-apis/im/v1/messages"
        payload = {
            "receive_id": receive_id,
            "msg_type": msg_type,
            "content": content,
            "uuid": str(uuid.uuid4()),
        }
        return self._send_request(
            url,
            params={"receive_id_type": receive_id_type},
            payload=payload,
        )
