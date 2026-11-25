"""Real client IP behind nginx and Cloudflare, trusting forwarded headers only from trusted proxies."""

import ipaddress
import os

CLOUDFLARE_RANGES = [
    "173.245.48.0/20", "103.21.244.0/22", "103.22.200.0/22", "103.31.4.0/22", "141.101.64.0/18",
    "108.162.192.0/18", "190.93.240.0/20", "188.114.96.0/20", "197.234.240.0/22", "198.41.128.0/17",
    "162.158.0.0/15", "104.16.0.0/13", "104.24.0.0/14", "172.64.0.0/13", "131.0.72.0/22",
    "2400:cb00::/32", "2606:4700::/32", "2803:f800::/32", "2405:b500::/32", "2405:8100::/32",
    "2a06:98c0::/29", "2c0f:f248::/32",
]
LOOPBACK_RANGES = ["127.0.0.0/8", "::1/128"]


def _networks(cidrs):
    return [ipaddress.ip_network(cidr.strip(), strict=False) for cidr in cidrs if cidr.strip()]


def _parse(raw):
    try:
        return ipaddress.ip_address(raw.strip())
    except ValueError:
        return None


CLOUDFLARE = _networks(CLOUDFLARE_RANGES)
TRUSTED = _networks(LOOPBACK_RANGES) + CLOUDFLARE + _networks(os.getenv("TRUSTED_PROXY_CIDRS", "").split(","))


def client_ip(request) -> str:
    """Peel trusted proxies off the right of X-Forwarded-For + REMOTE_ADDR; the first untrusted hop is the client."""
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")
    chain = [hop for raw in forwarded + [request.META.get("REMOTE_ADDR", "")] if (hop := _parse(raw))]
    peer = chain[-1] if chain else None
    if peer is None:
        return request.META.get("REMOTE_ADDR", "") or "0.0.0.0"
    if not any(peer in net for net in TRUSTED):
        return str(peer)

    cf_header = _parse(request.META.get("HTTP_CF_CONNECTING_IP", ""))
    if cf_header and any(peer in net for net in CLOUDFLARE):
        return str(cf_header)
    for hop in reversed(chain):
        if not any(hop in net for net in TRUSTED):
            return str(hop)
    return str(chain[0])
