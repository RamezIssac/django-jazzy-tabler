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


def client_ip(request) -> str:
    """Peel trusted proxies off the right of X-Forwarded-For + REMOTE_ADDR; the first untrusted hop is the client."""
    extra = _networks(os.getenv("TRUSTED_PROXY_CIDRS", "").split(","))
    cloudflare = _networks(CLOUDFLARE_RANGES)
    trusted = _networks(LOOPBACK_RANGES) + cloudflare + extra

    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")
    hops = [_parse(raw) for raw in forwarded + [request.META.get("REMOTE_ADDR", "")] if raw.strip()]
    chain = [hop for hop in hops if hop]
    peer = chain[-1] if chain else None
    if peer is None:
        return request.META.get("REMOTE_ADDR", "") or "0.0.0.0"
    if not any(peer in net for net in trusted):
        return str(peer)

    cf_header = _parse(request.META.get("HTTP_CF_CONNECTING_IP", ""))
    if cf_header and any(peer in net for net in cloudflare):
        return str(cf_header)
    for hop in reversed(chain):
        if not any(hop in net for net in trusted):
            return str(hop)
    return str(chain[0])
