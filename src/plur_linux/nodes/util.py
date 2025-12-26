from plur import base_shell
from plur import base_node
import random


class node:
    def __init__(self, guest):
        self.__dict__ = guest
        if 'iface_infos' in guest:
            self.vnets, self.ifaces = net(guest['iface_infos'])


def net(iface_infos):
    """
    >>> iface_infos = [ [ipgen('52:54:00:ff:11:{0}', '192.168.10.{0}/26', 9), 'br0.4084'], [ipgen('52:54:00:ff:50:{0}', '10.50.0.{0}/24', 221), 'br0.50'] ]
    >>> vnets, ifaces = net(iface_infos)
    >>> print vnets
    [{'bridge': 'br0.4084', 'mac': '52:54:00:ff:11:09'}, {'bridge': 'br0.50', 'mac': '52:54:00:ff:50:dd'}]
    >>> print ifaces
    [{'mac': '52:54:00:ff:11:09', 'name': 'eth0', 'hwaddr': '52:54:00:ff:11:09', 'ip': '192.168.10.9/26', 'route': [], 'up': True, 'mtu': '1500'}, {'mac': '52:54:00:ff:50:dd', 'name': 'eth1', 'hwaddr': '52:54:00:ff:50:dd', 'ip': '10.50.0.221/24', 'route': [], 'up': True, 'mtu': '1500'}]
    """
    vnets = []
    ifaces = []
    for i, iface in enumerate(iface_infos):
        if len(iface) > 2:
            vnet = {
                'mac': iface[0]['mac'],
                'bridge': iface[1],
                'type': iface[2]
            }
        else:
            vnet = {
                'mac': iface[0]['mac'],
                'bridge': iface[1]
            }
        vnets.append(vnet)
        ifa = {'name': 'eth{0}'.format(str(i))}
        ifa.update(iface[0])
        ifaces.append(ifa)
    return vnets, ifaces


def ipgen(mac_seg, ip_seg, ip_num, mtu='1500', options=[], routes=[], up=True):
    """
    >>> ipgen('52:54:00:ff:11:{0}', '192.168.10.{0}/24', 9)
    {'ip': '192.168.10.9/24', 'routes': [], 'up': True, 'mtu': '1500', 'mac': '52:54:00:ff:11:09', 'hwaddr': '52:54:00:ff:11:09', 'options': []}
    >>> ipgen('52:54:00:00:00:{0}', 'dhcp', 0, up=False)
    {'ip': 'dhcp', 'routes': [], 'up': False, 'mtu': '1500', 'mac': '52:54:00:00:00:00', 'hwaddr': '52:54:00:00:00:00', 'options': []}
    """
    mac_num = ('0' + hex(ip_num)[2:])[-2:]
    mac = mac_seg.format(mac_num)
    if ip_seg == 'dhcp':
        ip = 'dhcp'
    elif ip_seg is None:
        ip = None
    else:
        ip = ip_seg.format(str(ip_num))
    iface = {
        'mac': mac,
        'up': up,
        'ip': ip,
        'hwaddr': mac,
        'routes': routes,
        'mtu': mtu,
        'options': options
    }
    return iface


def service_on(service):
    return lambda session: base_shell.service_on(session, service)


def service_off(service):
    return lambda session: base_shell.service_off(session, service)


def run_scripts(scripts):
    return lambda session: [base_shell.run(session, s) for s in scripts]


def append_hosts(appends):
    return lambda session: [base_shell.run(session, 'echo "%s   %s  %s.r" >> /etc/hosts' % (a[0], a[1], a[1])) for a in appends]


def git_clone(project_dir, repos):
    actions = [
        'mkdir -p ' + project_dir,
        'cd ' + project_dir
    ]
    actions += ['git clone %s' % r for r in repos]
    return lambda session: [base_shell.run(session, a) for a in actions]


def session_info(username, hostname, password='', platform='centos'):
    sp = hostname.split('.')
    if len(sp) > 1:
        hostname = sp[0]
    return {
        'hostname': hostname,
        'username': username,
        'password': password,
        'waitprompt': base_node.get_linux_waitprompt(platform, hostname, username)
    }


def concat_dict(args):
    """
    >>> a = {'a': 'this is a'}
    >>> b = {'b': 'this is b'}
    >>> c = {'c': 'this is c'}
    >>> concat_dict([a, b, c])
    {'a': 'this is a', 'b': 'this is b', 'c': 'this is c'}
    """
    x = args[0]
    if len(args) == 1:
        return x
    return dict(x, **concat_dict(args[1:]))


def hex_mac_kvm():
    return [0x52, 0x54, 0x00,
            random.randint(0x00, 0xff),
            random.randint(0x00, 0xff),
            random.randint(0x00, 0xff)]


def MACprettyprint(mac):
    """
    >>> MACprettyprint([0x52, 0x54, 0x00, 0x00, 0x00, 0x00])
    '52:54:00:00:00:00'
    """
    return ':'.join(map(lambda x: "%02x" % x, mac))


def random_mac():
    return MACprettyprint(hex_mac_kvm())


def random_string(size=8):
    import string
    import random
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for i in range(size))


