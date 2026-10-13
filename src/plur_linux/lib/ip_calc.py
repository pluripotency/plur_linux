import ipaddress
from typing import Any, Union


class IPRangeError(ValueError):
    """Exception raised when an IP seed or target IP is out of the valid network range."""
    pass


IP_RANGE_ERROR_MSG = 'IP Range Error'


def calc_ip(
    network_with_prefix: str,
    seed: Union[int, str],
    with_prefix: bool = False,
    raise_on_error: bool = False,
) -> str:
    """Calculate an IPv4 address given a network CIDR and an IP seed.

    Supports:
    - seed as int (e.g. 1 -> network_address + 1)
    - seed as digit string (e.g. '1' -> network_address + 1)
    - seed as relative dot notation (e.g. '1.5' -> network_address + 1*256 + 5)
    - seed as full IPv4 address (e.g. '172.16.1.5')
    - seed as 'dhcp' (returns 'dhcp')

    Option B boundary rule:
    Valid usable host range is network_address < ip < broadcast_address (for prefixlen <= 30).
    Network address and broadcast address are treated as out-of-range ('IP Range Error').
    """
    def _handle_error(msg: str = IP_RANGE_ERROR_MSG) -> str:
        if raise_on_error:
            raise IPRangeError(msg)
        return msg

    if isinstance(seed, str) and seed.strip().lower() == 'dhcp':
        return 'dhcp'

    try:
        net = ipaddress.IPv4Network(str(network_with_prefix).strip(), strict=False)
    except Exception:
        return _handle_error(IP_RANGE_ERROR_MSG)

    try:
        if isinstance(seed, int):
            offset = seed
            target_int = int(net.network_address) + offset
            target_ip = ipaddress.IPv4Address(target_int)
        elif isinstance(seed, str):
            parts = seed.strip().split('.')
            if len(parts) == 1:
                offset = int(parts[0])
                target_int = int(net.network_address) + offset
                target_ip = ipaddress.IPv4Address(target_int)
            elif len(parts) == 4:
                target_ip = ipaddress.IPv4Address(seed.strip())
            elif len(parts) in (2, 3):
                offset = 0
                for part in parts:
                    val = int(part)
                    if val < 0 or val > 255:
                        return _handle_error(IP_RANGE_ERROR_MSG)
                    offset = offset * 256 + val
                target_int = int(net.network_address) + offset
                target_ip = ipaddress.IPv4Address(target_int)
            else:
                return _handle_error(IP_RANGE_ERROR_MSG)
        else:
            return _handle_error(IP_RANGE_ERROR_MSG)

        # Validate range (Option B: network_address < target_ip < broadcast_address)
        if net.prefixlen <= 30:
            if target_ip <= net.network_address or target_ip >= net.broadcast_address:
                return _handle_error(IP_RANGE_ERROR_MSG)
        else:
            # For point-to-point /31 or single host /32
            if target_ip not in net:
                return _handle_error(IP_RANGE_ERROR_MSG)

        if with_prefix:
            return f"{target_ip}/{net.prefixlen}"
        return str(target_ip)

    except Exception:
        return _handle_error(IP_RANGE_ERROR_MSG)


def get_segment_network(segment: dict[str, Any]) -> str:
    """Retrieve network_with_prefix from a segment dict, with fallback for backward compatibility."""
    if 'network_with_prefix' in segment and segment['network_with_prefix']:
        return str(segment['network_with_prefix']).strip()
    if 'ip_base_prefix' in segment and 'prefix' in segment:
        return f"{segment['ip_base_prefix']}.0/{segment['prefix']}"
    raise KeyError("Segment does not contain 'network_with_prefix' or 'ip_base_prefix'/'prefix'")


def get_ip_from_segment(
    segment: dict[str, Any],
    seed: Union[int, str],
    with_prefix: bool = False,
    raise_on_error: bool = False,
) -> str:
    """Calculate an IPv4 address for a given segment dict and seed."""
    network_with_prefix = get_segment_network(segment)
    return calc_ip(
        network_with_prefix,
        seed,
        with_prefix=with_prefix,
        raise_on_error=raise_on_error,
    )
