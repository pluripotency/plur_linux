from mini import misc
from plur import base_shell
from plur import session_wrap
PACKMAN_NOCONFIRM = 'pacman --noconfirm'

def pacman_update(session):
    base_shell.run(session, f'sudo {PACKMAN_NOCONFIRM} -Sy --needed archlinux-keyring && sudo {PACKMAN_NOCONFIRM}  -Syyu')

def pacman_install(packages):
    def func(session):
        base_shell.run(session, f'sudo {PACKMAN_NOCONFIRM} -Syy ' + ' '.join(packages))
    return func

def install_yay(session):
    pacman_install(misc.del_indent_lines("""
    git
    fakeroot
    binutils
    make
    gcc
    """))(session)
    base_shell.run(session, f'sudo {PACKMAN_NOCONFIRM} -S --needed git base-devel')
    _ = [base_shell.run(session, a) for a in misc.del_indent_lines("""
    git clone https://aur.archlinux.org/yay.git
    cd yay
    makepkg -si --noconfirm
    """)]

def install_hyprland(session):
    base_shell.run(session, 'yay -S ' + ' '.join(misc.del_indent_lines("""
    hyprland
    dolphin
    wofi
    hyprpaper
    kitty
    """)))

def set_jp106(session):
    base_shell.run(session, 'sudo localectl set-keymap jp106')

def systemd_networkd_str(ip_with_prefix, gw, dns_list, domain='local', ifname='eth0'):
    """
    https://wiki.archlinux.jp/index.php/Systemd-networkd
    """
    if ip_with_prefix == 'dhcp':
        contents = misc.del_indent_lines(f"""
        [Match]
        Name={ifname}

        [Network]
        DHCP=yes
        """)
    else:
        contents = misc.del_indent_lines(f"""
        [Match]
        Name={ifname}

        [Address]
        Address={ip_with_prefix}

        [Network]
        DHCP=no
        DNS={' '.join(dns_list)}
        Domain={domain}

        [Route]
        Gateway={gw}
        """)
    return contents

def systemd_networkd(ip_with_prefix, gw, dns_list, domain='local', ifname='eth0'):
    contents = systemd_networkd_str(ip_with_prefix, gw, dns_list, domain, ifname)
    netd_dir = '/etc/systemd/network'
    net20 = f'{netd_dir}/20-{ifname}.network'

    @session_wrap.sudo
    def func(session):
        base_shell.run(session, f"rm -f {netd_dir}/10-cloud*")
        base_shell.here_doc(session, net20, contents)
        base_shell.run(session, 'systemctl restart systemd-networkd')
    return func

def test_systemd_networkd():
    return systemd_networkd('192.168.0.50/24', '192.168.0.1', ['8.8.8.8', '8.8.4.4'])

def configure_network(ifaces):
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
    """
    iface = ifaces[0]
    ifname = iface['con_name']
    ip_with_prefix = iface['ip']
    gw = ''
    if 'gateway' in iface:
        gw = iface['gateway']
    dns_list = []
    if 'nameservers' in iface:
        dns_list = iface['nameservers']
    domain = 'local'
    if 'search' in iface:
        domain = iface['search']
    return systemd_networkd(ip_with_prefix, gw, dns_list, domain, ifname)

    
