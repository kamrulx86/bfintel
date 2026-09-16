import json

import httpx

from app.models.notification_channel import NotificationChannel


def send_to_channel(channel: NotificationChannel, config: dict, message: str) -> tuple[bool, str | None]:
    ctype = channel.channel_type
    if ctype == "telegram":
        token = config.get("bot_token")
        chat_id = config.get("chat_id")
        if not token or not chat_id:
            return False, "missing bot_token or chat_id"
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try:
            with httpx.Client(timeout=12.0) as client:
                resp = client.post(url, json={"chat_id": chat_id, "text": message[:4000]})
                if resp.status_code >= 400:
                    return False, resp.text[:500]
        except Exception as exc:  # noqa: BLE001
            return False, str(exc)
        return True, None

    if ctype == "slack":
        webhook = config.get("webhook_url")
        if not webhook:
            return False, "missing webhook_url"
        try:
            with httpx.Client(timeout=12.0) as client:
                resp = client.post(webhook, json={"text": message[:4000]})
                if resp.status_code >= 400:
                    return False, resp.text[:500]
        except Exception as exc:  # noqa: BLE001
            return False, str(exc)
        return True, None

    if ctype == "webhook":
        url = config.get("url")
        if not url:
            return False, "missing url"
        headers = {"Content-Type": "application/json"}
        if config.get("auth_header"):
            headers["Authorization"] = config["auth_header"]
        body = {"text": message, "source": "bfintel"}
        try:
            with httpx.Client(timeout=12.0) as client:
                resp = client.post(url, content=json.dumps(body), headers=headers)
                if resp.status_code >= 400:
                    return False, resp.text[:500]
        except Exception as exc:  # noqa: BLE001
            return False, str(exc)
        return True, None

    return False, f"unsupported channel type: {ctype}"
