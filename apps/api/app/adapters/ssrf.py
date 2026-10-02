import ipaddress
import socket
from urllib.parse import urlparse
from app.core.config import get_settings
from app.core.errors import SSRFSecurityError


def validate_target_url(url: str) -> None:
    settings = get_settings()
    if settings.SSRF_ALLOW_PRIVATE_IPS:
        return

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise SSRFSecurityError(f"Unsupported URL scheme: {parsed.scheme}")

    hostname = parsed.hostname
    if not hostname:
        raise SSRFSecurityError("Target URL is missing a valid hostname")

    # Resolve all A/AAAA records
    try:
        addr_info = socket.getaddrinfo(hostname, None)
    except socket.gaierror as e:
        raise SSRFSecurityError(f"Failed to resolve host '{hostname}': {e}") from e

    for item in addr_info:
        ip_str = item[4][0]
        ip = ipaddress.ip_address(ip_str)

        # Check for loopback, private, link-local, multicast, or reserved
        if (
            ip.is_loopback
            or ip.is_private
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
        ):
            raise SSRFSecurityError(
                f"Target address '{hostname}' resolves to restricted IP '{ip_str}'"
            )
