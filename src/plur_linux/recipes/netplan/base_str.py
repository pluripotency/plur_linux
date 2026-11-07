from mini import misc
from plur_linux.recipes.netplan import lib as netplan_lib
hier_space = netplan_lib.hier_space

def create_address_str(ipv4_with_prefix, gw=None, nameservers=None):
    """
    >>> gen_str = create_address_str("192.168.0.70/24", "192.168.0.1", ["8.8.8.8", "8.8.4.4"])
    >>> print(gen_str) # doctest: +REPORT_NDIFF
          addresses:
          - "192.168.0.70/24"
          routes:
          - to: "default"
            via: "192.168.0.1"
          nameservers:
            addresses:
            - 8.8.8.8
            - 8.8.4.4
    """
    netplan_str = ' ' * 6 + "addresses:"
    netplan_str += hier_space(6, f'- "{ipv4_with_prefix}"')
    if gw:
        netplan_str += hier_space(6, "routes:")
        netplan_str += hier_space(6, '- to: "default"')
        netplan_str += hier_space(6, f'  via: "{gw}"')
    if isinstance(nameservers, list):
        netplan_str += hier_space(6, "nameservers:")
        netplan_str += hier_space(8, "addresses:")
        for ns in nameservers:
            netplan_str += hier_space(8, f"- {ns}")
    return netplan_str

def create_ipv6_str():
    """
    >>> gen_str = create_ipv6_str()
    >>> print(gen_str) # doctest: +REPORT_NDIFF
          dhcp6: false
          accept-ra: false
          link-local: []
    """
    return misc.del_indent("""
          dhcp6: false
          accept-ra: false
          link-local: []
    """)

def create_renderer_str(renderer='networkd'):
    """
    >>> gen_str = create_renderer_str()
    >>> print(gen_str) # doctest: +REPORT_NDIFF
    network:
      version: 2
      renderer: networkd
    """
    return misc.del_indent(f"""
    network:
      version: 2
      renderer: {renderer}
    """)

def create_if_str(ifname, mac=None):
    """
    >>> gen_str = create_ethernet_str("eno1")
    >>> print(gen_str) # doctest: +REPORT_NDIFF
        eno1:
          dhcp4: false
          dhcp6: false
          accept-ra: false
          link-local: []
    """
    if_str = ' ' * 4 + f'{ifname}:'
    if mac:
        if_str += hier_space(6, 'match:')
        if_str += hier_space(8, f'macaddress: {mac}')
    if_str += hier_space(6, f'set-name: {ifname}')
    if_str += hier_space(6, 'dhcp4: true\n') + create_ipv6_str()
    return if_str

def create_base_str(ifname):
    """
    >>> gen_str = create_base_str("eno1")
    >>> print(gen_str) # doctest: +REPORT_NDIFF
    network:
      version: 2
      renderer: networkd
      ethernets:
        eno1:
          dhcp4: false
          dhcp6: false
          accept-ra: false
          link-local: []
    """
    return misc.del_indent(f"""
    network:
      version: 2
      renderer: networkd
      ethernets:
        {ifname}:
          dhcp4: false\n
    """) + create_ipv6_str()

def create_dhcp4_str(ifname):
    """
    >>> gen_str = create_dhcp4_str("eno1")
    >>> print(gen_str) # doctest: +REPORT_NDIFF
    network:
      version: 2
      renderer: networkd
      ethernets:
        eno1:
          dhcp4: true
          dhcp6: false
          accept-ra: false
          link-local: []
    """
    return misc.del_indent(f"""
    network:
      version: 2
      renderer: networkd
      ethernets:
        {ifname}:
          dhcp4: true\n
    """) + create_ipv6_str()
