import re
from plur import base_shell
from plur import ansi_colors
from . import nmcli_str


def con_mod_ipv4_str_list(iface):
    con_name = iface['con_name'] if 'con_name' in iface else iface['name'] if 'name' in iface else False

    con_mod = f'nmcli con mod {con_name}'
    commands = []

    one_line = ''
    autoconnect = True
    if 'autoconnect' in iface and iface['autoconnect'] is False:
        autoconnect = False
    one_line += f' c.autoconnect yes' if autoconnect else ' c.autoconnect no'

    if 'mtu' in iface and re.match('\d{2,5}', iface['mtu']):
        one_line += f' 802-3-ethernet.mtu {str(iface["mtu"])}'
    if one_line != '':
        commands += [con_mod + one_line]

    two_line = ' ipv4.method disabled'
    if 'ip' in iface:
        ip = iface['ip']
        if ip is None:
            pass
        elif re.match('(\d{1,3}\.){3}\d{1,3}/\d{1,2}', ip):
            two_line = f' ipv4.method manual ipv4.address {ip}'
            if 'gateway' in iface:
                two_line += f' ipv4.gateway ' + iface['gateway']
        elif ip == 'dhcp':
            two_line = ' ipv4.method auto'
            if 'ignore_auto_dns' in iface:
                two_line += ' ipv4.ignore-auto-dns yes'
                two_line += ' ipv4.ignore-auto-routes yes'
            else:
                two_line += ' ipv4.ignore-auto-dns no'
                two_line += ' ipv4.ignore-auto-routes no'
        else:
            print(ansi_colors.red(f'err in con_mod_ipv4_str: wrong ip format: {ip}'))
            exit(1)
    commands += [con_mod + two_line]

    three_line = ''
    if 'nameservers' in iface:
        nameservers = iface['nameservers']
        if isinstance(nameservers, list) and len(nameservers) > 0:
            ns = ' '.join(nameservers)
            three_line += f' ipv4.dns "{ns}"'
    if 'search' in iface:
        three_line += f' ipv4.dns-search {iface["search"]}'
    if 'routes' in iface:
        routes = iface['routes']
        if isinstance(routes, list) and len(routes) > 0:
            # one route is "192.168.0.0/24 192.168.1.254"
            three_line += f' ipv4.routes "{routes[0]}"'
            if len(routes) > 1:
                for route in routes[1:]:
                    three_line += f' +ipv4.routes "{route}"'
    if three_line != '':
        commands += [con_mod + three_line]
    return commands


def install_nm_if_not_installed(session):
    if not base_shell.check_command_exists(session, 'nmcli'):
        service = 'NetworkManager'
        base_shell.yum_install(session, {'packages': [service]})
        base_shell.service_on(session, service)


def remove_down_nm_entries(session):
    con_capture = base_shell.run(session, 'nmcli con | cat')
    for line in con_capture.splitlines():
        con_uuid = nmcli_str.get_down_con_uuid(line)
        if con_uuid:
            base_shell.run(session, f'nmcli c del "{con_uuid}"')


def remove_duped_entries(session, iface_list):
    con_capture = base_shell.run(session, 'nmcli con | cat')
    con_name_list = [iface['con_name'] if 'con_name' in iface else iface['name'] if 'name' in iface else False for iface in iface_list]
    for line in con_capture.splitlines():
        for ifconname in con_name_list:
            con_uuid = nmcli_str.get_conname_con_uuid(line, ifconname)
            if con_uuid:
                base_shell.run(session, f'nmcli c del "{con_uuid}"')
            con_uuid = nmcli_str.get_ifname_con_uuid(line, ifconname)
            if con_uuid:
                base_shell.run(session, f'nmcli c del "{con_uuid}"')


def configure(session, iface):
    con_name = iface['con_name'] if 'con_name' in iface else iface['name'] if 'name' in iface else False
    base_shell.run(session, nmcli_str.con_add(con_name))
    [base_shell.run(session, cmd) for cmd in con_mod_ipv4_str_list(iface)]
    base_shell.run(session, nmcli_str.con_up(con_name))
