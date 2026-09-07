import ipaddress
import re
from mini import misc
from plur import session_wrap
from plur import base_shell
from plur_linux.recipes import firewalld
from plur_linux.lib.env_ops import EnvSegments, get_segment_network, get_ip_from_segment


def calc_dhcp_range(net: ipaddress.IPv4Network):
    """
    Calculate DHCP range: the last 1/4 of the segment, excluding the broadcast
    and the last 4 usable host IPs.
    For example, for 192.168.0.0/24 (256 addresses):
    - 3/4 offset is 192 -> 192.168.0.192
    - broadcast - 5 is 192.168.0.250 (excluding .251, .252, .253, .254 and broadcast .255)
    If start_ip > end_ip (e.g. very small subnets like /29 or smaller), fallback to usable host range.
    """
    total = net.num_addresses
    start_ip = net.network_address + (total * 3 // 4)
    end_ip = net.broadcast_address - 5
    if start_ip > end_ip or start_ip <= net.network_address:
        start_ip = net.network_address + 1
        end_ip = net.broadcast_address - 1
    return str(start_ip), str(end_ip)


def find_segment_for_ip(ip_str, segments=None):
    """
    Find which segment in env_ops contains the given ip_str.
    """
    if segments is None:
        try:
            segments = EnvSegments().get_segment_list()
        except Exception:
            segments = []
    try:
        ip = ipaddress.IPv4Address(ip_str.split('/')[0])
    except (ValueError, AttributeError):
        return None

    for seg in segments:
        net_str = get_segment_network(seg)
        if net_str:
            try:
                net = ipaddress.IPv4Network(net_str, strict=False)
                if ip in net:
                    return seg
            except ValueError:
                continue
    return None


def create_subnet_params_from_segment(segment):
    """
    Build subnet_params dict from an env_ops segment dictionary.
    """
    net_str = get_segment_network(segment)
    net = ipaddress.IPv4Network(net_str, strict=False)
    dhcp_start, dhcp_end = calc_dhcp_range(net)
    gateway_seed = segment.get('gateway_seed', '1')
    gateway = get_ip_from_segment(segment, gateway_seed)
    nameservers = segment.get('nameservers', '8.8.8.8')
    domain_name = segment.get('search', 'local')

    return {
        'subnet': str(net.network_address),
        'netmask': str(net.netmask),
        'gateway': gateway,
        'nameservers': nameservers,
        'dh_range': f"{dhcp_start} {dhcp_end}",
        'broadcast': str(net.broadcast_address),
        'domain_name': domain_name,
        'domain_name_servers': nameservers.split(',')[0].strip() if nameservers else 'a8pxe.local',
        'allowed_net': f"{net.network_address}/{net.prefixlen}",
    }


def get_subnet_params(pxe_ip=None, segment=None, segments=None):
    """
    Determine subnet_params from segment or pxe_ip (looking up in segments).
    Falls back to dynamic /24 or predefined defaults if not found.
    """
    if segment is not None:
        if isinstance(segment, dict):
            return create_subnet_params_from_segment(segment)
        if isinstance(segment, str):
            if segments is None:
                try:
                    segments = EnvSegments().get_segment_list()
                except Exception:
                    segments = []
            for seg in segments:
                if seg.get('net_source') == segment or get_segment_network(seg) == segment:
                    return create_subnet_params_from_segment(seg)

    if pxe_ip:
        found = find_segment_for_ip(pxe_ip, segments=segments)
        if found:
            return create_subnet_params_from_segment(found)

        # Fallback if pxe_ip is not in segments
        clean_ip = pxe_ip.split('/')[0]
        if re.search(r'^192\.168\.0\.', clean_ip):
            net = ipaddress.IPv4Network('192.168.0.0/24')
            dhcp_start, dhcp_end = calc_dhcp_range(net)
            return {
                'subnet': '192.168.0.0',
                'netmask': '255.255.255.0',
                'gateway': '192.168.0.1',
                'nameservers': '8.8.8.8',
                'dh_range': f"{dhcp_start} {dhcp_end}",
                'broadcast': '192.168.0.255',
                'allowed_net': '192.168.0.0/24',
            }
        elif re.search(r'^192\.168\.10\.', clean_ip):
            net = ipaddress.IPv4Network('192.168.10.0/24')
            dhcp_start, dhcp_end = calc_dhcp_range(net)
            return {
                'subnet': '192.168.10.0',
                'netmask': '255.255.255.0',
                'gateway': '192.168.10.62',
                'nameservers': '192.168.10.1',
                'dh_range': f"{dhcp_start} {dhcp_end}",
                'broadcast': '192.168.10.255',
                'allowed_net': '192.168.10.0/24',
            }
        else:
            try:
                net = ipaddress.IPv4Interface(f"{clean_ip}/24").network
                dhcp_start, dhcp_end = calc_dhcp_range(net)
                return {
                    'subnet': str(net.network_address),
                    'netmask': str(net.netmask),
                    'gateway': str(net.network_address + 1),
                    'nameservers': '8.8.8.8',
                    'dh_range': f"{dhcp_start} {dhcp_end}",
                    'broadcast': str(net.broadcast_address),
                    'allowed_net': f"{net.network_address}/{net.prefixlen}",
                }
            except Exception:
                pass

    return ex_subnet_params.copy()


def create_pre_str(domain_name='local', domain_name_servers='a8pxe.local'):
    """
    >>> a = create_pre_str()
    >>> print(a)
    option domain-name     "local";
    option domain-name-servers     a8pxe.local;
    default-lease-time 600;
    max-lease-time 7200;
    <BLANKLINE>
    authoritative;
    <BLANKLINE>
    """
    value = misc.del_indent(f"""
    option domain-name     "{domain_name}";
    option domain-name-servers     {domain_name_servers};
    default-lease-time 600;
    max-lease-time 7200;

    authoritative;

    """)
    return value


ex_subnet_params = {
    'subnet': '192.168.10.0',
    'netmask': '255.255.255.0',
    'gateway': '192.168.10.62',
    'nameservers': '192.168.10.1',
    'dh_range': '192.168.10.190 192.168.10.199',
    'broadcast': '192.168.10.255',
}


def extract_subnet_params(subnet_params):
    subnet = subnet_params['subnet']
    netmask = subnet_params['netmask']
    gateway = subnet_params['gateway']
    nameservers = subnet_params['nameservers']
    dh_range = subnet_params['dh_range']
    broadcast = subnet_params['broadcast']
    return [
        subnet,
        netmask,
        gateway,
        nameservers,
        dh_range,
        broadcast
    ]


def create_subnet_str(subnet_params, close_last=True):
    """
    >>> print(create_subnet_str(ex_subnet_params))
    subnet 192.168.10.0 netmask 255.255.255.0 {
        range dynamic-bootp        192.168.10.190 192.168.10.199;
        option broadcast-address   192.168.10.255;
        option routers             192.168.10.62;
        option domain-name-servers 192.168.10.1;
    }
    <BLANKLINE>
    """
    [
        subnet,
        netmask,
        gateway,
        nameservers,
        dh_range,
        broadcast
    ] = extract_subnet_params(subnet_params)
    value = f'subnet {subnet} netmask {netmask}' + ' {\n' + misc.del_indent(f"""
        range dynamic-bootp        {dh_range};
        option broadcast-address   {broadcast};
        option routers             {gateway};
        option domain-name-servers {nameservers};
    """)
    if close_last:
        value += '\n}\n'
    return value


def create_dhcp_conf_str(subnet_params):
    """
    >>> a = create_dhcp_conf_str(ex_subnet_params)
    >>> print(a)
    option domain-name     "local";
    option domain-name-servers     a8pxe.local;
    default-lease-time 600;
    max-lease-time 7200;
    <BLANKLINE>
    authoritative;
    subnet 192.168.10.0 netmask 255.255.255.0 {
        range dynamic-bootp        192.168.10.190 192.168.10.199;
        option broadcast-address   192.168.10.255;
        option routers             192.168.10.62;
        option domain-name-servers 192.168.10.1;
    }
    <BLANKLINE>
    """
    domain_name = subnet_params.get('domain_name', 'local')
    domain_name_servers = subnet_params.get('domain_name_servers', 'a8pxe.local')
    return create_pre_str(domain_name=domain_name, domain_name_servers=domain_name_servers) + create_subnet_str(subnet_params)


def create_pxe_pre_str(domain_name='local', domain_name_servers='a8pxe.local'):
    """
    >>> a = create_pxe_pre_str()
    >>> print(a)
    option domain-name     "local";
    option domain-name-servers     a8pxe.local;
    default-lease-time 600;
    max-lease-time 7200;
    <BLANKLINE>
    authoritative;
    <BLANKLINE>
    option space pxelinux;
    option pxelinux.magic code 208 = string;
    option pxelinux.configfile code 209 = text;
    option pxelinux.pathprefix code 210 = text;
    option pxelinux.reboottime code 211 = unsigned integer 32;
    option architecture-type code 93 = unsigned integer 16;
    <BLANKLINE>
    <BLANKLINE>
    """
    value = create_pre_str(domain_name=domain_name, domain_name_servers=domain_name_servers) + misc.del_indent("""
    
    option space pxelinux;
    option pxelinux.magic code 208 = string;
    option pxelinux.configfile code 209 = text;
    option pxelinux.pathprefix code 210 = text;
    option pxelinux.reboottime code 211 = unsigned integer 32;
    option architecture-type code 93 = unsigned integer 16;


    """)
    return value


def create_pxe_dhcp_subnet_str(pxe_ip, subnet_params):
    """
    >>> a = create_pxe_dhcp_subnet_str('192.168.10.154', ex_subnet_params)
    >>> print(a)
    subnet 192.168.10.0 netmask 255.255.255.0 {
        range dynamic-bootp        192.168.10.190 192.168.10.199;
        option broadcast-address   192.168.10.255;
        option routers             192.168.10.62;
        option domain-name-servers 192.168.10.1;
        class "pxeclients" {
            match if substring (option vendor-class-identifier, 0, 9) = "PXEClient";
            next-server 192.168.10.154;
            if option architecture-type = 00:07 {
                filename "BOOTX64.EFI";
            }
            else {
                filename "pxelinux.0";
            }
        }
    }
    <BLANKLINE>
    """
    value = create_subnet_str(subnet_params, close_last=False)
    value += misc.del_indent("""
    
        class "pxeclients" {
            match if substring (option vendor-class-identifier, 0, 9) = "PXEClient";
    """)
    value += f'\n        next-server {pxe_ip};'
    value += misc.del_indent("""

            if option architecture-type = 00:07 {
                filename "BOOTX64.EFI";
            }
            else {
                filename "pxelinux.0";
            }
        }
    """)
    value += '\n}\n'
    return value


def create_pxe_dhcp_conf_str(pxe_ip, subnet_params):
    """
    >>> print(create_pxe_dhcp_conf_str('192.168.10.154', ex_subnet_params))
    option domain-name     "local";
    option domain-name-servers     a8pxe.local;
    default-lease-time 600;
    max-lease-time 7200;
    <BLANKLINE>
    authoritative;
    <BLANKLINE>
    option space pxelinux;
    option pxelinux.magic code 208 = string;
    option pxelinux.configfile code 209 = text;
    option pxelinux.pathprefix code 210 = text;
    option pxelinux.reboottime code 211 = unsigned integer 32;
    option architecture-type code 93 = unsigned integer 16;
    <BLANKLINE>
    subnet 192.168.10.0 netmask 255.255.255.0 {
        range dynamic-bootp        192.168.10.190 192.168.10.199;
        option broadcast-address   192.168.10.255;
        option routers             192.168.10.62;
        option domain-name-servers 192.168.10.1;
        class "pxeclients" {
            match if substring (option vendor-class-identifier, 0, 9) = "PXEClient";
            next-server 192.168.10.154;
            if option architecture-type = 00:07 {
                filename "BOOTX64.EFI";
            }
            else {
                filename "pxelinux.0";
            }
        }
    }
    <BLANKLINE>
    """
    domain_name = subnet_params.get('domain_name', 'local')
    domain_name_servers = subnet_params.get('domain_name_servers', 'a8pxe.local')
    return create_pxe_pre_str(domain_name=domain_name, domain_name_servers=domain_name_servers) + create_pxe_dhcp_subnet_str(pxe_ip, subnet_params)


def setup(subnet_params=None, set_fw=True, pxe_ip=False, segment=None):
    if subnet_params is None:
        subnet_params = get_subnet_params(pxe_ip=pxe_ip if pxe_ip else None, segment=segment)

    @session_wrap.sudo
    def func(session):
        if set_fw:
            firewalld.configure(services=['dhcp'], add=True)(session)
        base_shell.run(session, 'dnf install -y dhcp-server')
        conf_path = '/etc/dhcp/dhcpd.conf'
        if pxe_ip:
            contents = create_pxe_dhcp_conf_str(pxe_ip, subnet_params)
        else:
            contents = create_dhcp_conf_str(subnet_params)
        base_shell.here_doc(session, conf_path, contents.split('\n'))
        base_shell.run(session, 'systemctl enable --now dhcpd')
    return func

