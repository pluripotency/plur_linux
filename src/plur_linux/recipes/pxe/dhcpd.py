from mini import misc
from plur import session_wrap
from plur import base_shell
from recipes import firewalld


def create_pre_str():
    """
    >>> a = create_pre_str()()
    >>> print(a)
    option domain-name     "local";
    option domain-name-servers     a8pxe.local;
    default-lease-time 600;
    max-lease-time 7200;
    <BLANKLINE>
    authoritative;
    <BLANKLINE>
    """
    domain_name = 'local'
    domain_name_servers = 'a8pxe.local'
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
    return create_pre_str() + create_subnet_str(subnet_params)


def create_pxe_pre_str():
    """
    >>> a = create_pxe_pre_str()
    >>> print(a)
    option domain-name     "local";
    option domain-name-servers     dlp.local;
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
    value = create_pre_str() + misc.del_indent("""
    
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
    return create_pxe_pre_str() + create_pxe_dhcp_subnet_str(pxe_ip, subnet_params)


def setup(subnet_params, set_fw=True, pxe_ip=False):
    @session_wrap.sudo
    def func(session):
        if set_fw:
            firewalld.configure(services=['dhcp'], add=True)
        base_shell.run(session, 'dnf install -y dhcp-server')
        conf_path = '/etc/dhcp/dhcpd.conf'
        if pxe_ip:
            contents = create_pxe_dhcp_conf_str(pxe_ip, subnet_params)
        else:
            contents = create_dhcp_conf_str(subnet_params)
        base_shell.here_doc(session, conf_path, contents.split('\n'))
        base_shell.run(session, 'systemctl enable --now dhcpd')
    return func

