from __future__ import annotations

from urllib.parse import urlparse

from .models import PreviewRef


def classify_preview_url(url: str | None) -> PreviewRef:
    if not url:
        return PreviewRef(url=None, kind="proof_managed_localhost")

    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()

    if hostname in {"localhost", "127.0.0.1", "::1"}:
        kind = "localhost"
    elif hostname.endswith(".ts.net") or hostname.startswith("100."):
        kind = "tailnet"
    elif hostname.startswith("192.168.") or hostname.startswith("10."):
        kind = "lan"
    elif "preview" in hostname:
        kind = "deployment_preview"
    else:
        kind = "remote"

    return PreviewRef(url=url, kind=kind)
