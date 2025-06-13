from mini import misc
from plur import base_shell
from plur import session_wrap
from . import ops


def join_n(lines):
    return "\n".join(lines)


def create_ipv6_lines():
    """
    >>> print(join_n(create_ipv6_lines()))
          dhcp6: false
          accept-ra: false
          link-local: []
    """
    return misc.del_indent_lines(f"""
          dhcp6: false
          accept-ra: false
          link-local: []
    """)


def create_static_ip_lines(ip, gw, nameservers):
    """
    >>> print(join_n(create_static_ip_lines('192.168.0.1/24', '192.168.0.254', ['8.8.8.8', '8.8.4.4'])))
          addresses: [192.168.0.1/24]
          routes:
            - to: default
              via: 192.168.0.254
              metric: 100
          nameservers:
            addresses: [8.8.8.8,8.8.4.4]
          dhcp4: false
    """
    ns_str = ",".join(nameservers)
    return misc.del_indent_lines(f"""
          addresses: [{ip}]
          routes:
            - to: default
              via: {gw}
              metric: 100
          nameservers:
            addresses: [{ns_str}]
          dhcp4: false
    """)


def netplan_pre_str(renderer="networkd"):
    return misc.del_indent_lines(f"""
    network:
      version: 2
      renderer: {renderer}
    """)


def create_net_plan(session, netplan_lines):
    netplan_dir = "/etc/netplan"
    netplan_path = f"{netplan_dir}/51-ip.yaml"
    base_shell.here_doc(session, netplan_path, netplan_lines, eof="EOF")
    base_shell.run(session, f"rm -f {netplan_dir}/50-cloud-init.yaml")
    base_shell.run(session, f"chmod 600 {netplan_dir}/*")


def configure_netplan(ifaces):
    @session_wrap.sudo
    def func(session):
        netplan_lines = netplan_pre_str()
        netplan_lines += ["  ethernets:"]
        for i, iface in enumerate(ifaces):
            base_shell.run(session, f"IFACE=`ip l | egrep ^{i + 2}: |" + " awk '{print $2}' | cut -d: -f1`")
            base_shell.run(session, "IFMAC=`ip -br l | egrep ^$IFACE | awk '{print $3}'`")
            netplan_lines += misc.del_indent_lines("""
                $IFACE:
                  match:
                      macaddress: $IFMAC
                  set-name: $IFACE
            """)
            if iface["ip"] == "dhcp":
                netplan_lines += ["      dhcp4: true"]
                netplan_lines += create_ipv6_lines()
            else:
                ip = iface["ip"]
                gw = iface["gateway"]
                nameservers = iface["nameservers"]
                netplan_lines += create_static_ip_lines(ip, gw, nameservers)
                netplan_lines += create_ipv6_lines()
        create_net_plan(session, netplan_lines)
        base_shell.run(session, "netplan apply")

    return func


def configure(node):
    """
    ifaces = [{
        'con_name': 'eth0',
        'autoconnect': True,
        'ip': '10.10.10.10/24',
        'gateway': '10.10.10.254',
        'nameservers': ['dns1', 'dns2'],
        'search': 'r',
        'routes': ['192.168.0.0/24 10.10.10.254']
    }, {
        'con_name': 'eth1',
        'autoconnect': True,
        'ip': 'dhcp',
        'ignore_auto_dns': False,
        'ignore_auto_routes': False
    }]
    """
    def func(session):
        if hasattr(node, 'ifaces'):
            ifaces = node.ifaces
            if base_shell.check_command_exists(session, 'nmcli'):
               configure_by_nmcli(ifaces)(session)
            else:
               #use_nm = get_y_n('use NetworkManager')
               #if use_nm:
               #    netplan.setup_nm(session)
               #    netplan.configure_by_nmcli(node)(session)
               #else:
               configure_netplan(ifaces)(session)
    return func


def setup_nm(session):
    ops.sudo_apt_get_install_y(["network-manager"])(session)
    base_shell.here_doc(session, "/etc/NetworkManager/conf.d/manage-all.conf", misc.del_indent_lines("""
    [keyfile]
    unmanaged-devices=none
    """),
    )
    base_shell.run(session, "sudo systemctl enable --now NetworkManager")
    [
        base_shell.run(session, a)
        for a in misc.del_indent_lines("""
    sudo systemctl disable --now systemd-networkd.service systemd-networkd.socket networkd-dispatcher.service 
    sudo systemctl restart NetworkManager
    sudo apt purge netplan netplan.io -y
    sudo rm -rf /etc/netplan
    """)
    ]
    base_shell.run(session, "reset")


def configure_by_nmcli(ifaces):
    from plur_linux.recipes.net import nmcli
    @session_wrap.sudo
    def func(session):
        nmcli.remove_duped_entries(session, ifaces)
        for i, iface in enumerate(ifaces):
            base_shell.run(session, f"IFACE=`ip l | egrep ^{i + 2}: |" + " awk '{print $2}' | cut -d: -f1`")
            iface["con_name"] = "$IFACE"
            nmcli.configure(session, iface)

    return func
