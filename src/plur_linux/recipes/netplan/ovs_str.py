from mini import misc
from plur_linux.recipes.netplan import lib as netplan_lib
hier_space = netplan_lib.hier_space

def create_ovs_str(ifname, brname, ipv4_with_prefix=None, gw=None, nameservers=None):
    """
    # /etc/netplan/50-ovs.yaml
    >>> ovs_str = create_ovs_str("eno1", "br0", "192.168.0.70/24", "192.168.0.1", ["8.8.8.8", "8.8.4.4"])
    >>> print(ovs_str) # doctest: +REPORT_NDIFF
    network:
      version: 2
      renderer: networkd
      ethernets:
        eno1:
          dhcp4: false
          dhcp6: false
      bridges:
        br0:
          interfaces:
          - eno1
          addresses:
          - "192.168.0.70/24"
          routes:
          - to: "default"
            via: "192.168.0.1"
          nameservers:
            addresses:
            - 8.8.8.8
            - 8.8.4.4
          openvswitch: {}
    """
    netplan_str = misc.del_indent(f"""
    network:
      version: 2
      renderer: networkd
      ethernets:
        {ifname}:
          dhcp4: false
          dhcp6: false
      bridges:
        {brname}:
          interfaces:
          - {ifname}
    """)
    if ipv4_with_prefix:
        netplan_str += hier_space(6, "addresses:")
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
    netplan_str += hier_space(6, 'openvswitch: {}')
    return netplan_str
