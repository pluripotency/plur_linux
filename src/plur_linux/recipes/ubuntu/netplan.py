from mini import misc
from plur import base_shell
from plur import session_wrap
from . import ops

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
               from plur_linux.recipes.netplan import base as netplan_base
               netplan_base.configure_netplan(ifaces)(session)
    return func

def setup_nm_til_23(session):
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

def setup_nm(session):
    ops.sudo_apt_get_install_y(["network-manager"])(session)
    oneliner = "sudo sed -i 's/renderer:\s*networkd/renderer: NetworkManager/g' /etc/netplan/*.yaml && sudo netplan apply"
    base_shell.run(session, oneliner)
    [base_shell.run(session, a) for a in misc.del_indent_lines("""
    sudo systemctl stop systemd-networkd systemd-networkd.socket
    sudo systemctl disable systemd-networkd systemd-networkd.socket
    sudo systemctl mask systemd-networkd systemd-networkd.socket
    sudo systemctl disable systemd-networkd-wait-online.service
    sudo systemctl mask systemd-networkd-wait-online.service
    """)]
    # base_shell.run(session, "sudo systemctl enable --now NetworkManager")
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
