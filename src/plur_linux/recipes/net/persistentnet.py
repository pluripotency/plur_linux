from plur import base_shell
from plur import session_wrap
import re

udev_str = lambda ifname, mac: 'SUBSYSTEM=="net", ACTION=="add", ATTR{address}=="%s", NAME="%s"' % (mac, ifname)

dev16_dev_list = map(lambda x: re.split(r'\s+', x), filter(lambda x: re.match('^eth.+', x), """
eth0    94:18:82:00:23:18
eth1    94:18:82:00:23:19
eth2    94:18:82:00:23:1a
eth3    94:18:82:00:23:1b
eth4    38:ea:a7:10:40:ee
eth5    38:ea:a7:10:40:ef
""".split('\n')))

dev16_result = '\n'.join(filter(lambda x: re.match('^SUB.+', x), """
SUBSYSTEM=="net", ACTION=="add", ATTR{address}=="94:18:82:00:23:18", NAME="eth0"
SUBSYSTEM=="net", ACTION=="add", ATTR{address}=="94:18:82:00:23:19", NAME="eth1"
SUBSYSTEM=="net", ACTION=="add", ATTR{address}=="94:18:82:00:23:1a", NAME="eth2"
SUBSYSTEM=="net", ACTION=="add", ATTR{address}=="94:18:82:00:23:1b", NAME="eth3"
SUBSYSTEM=="net", ACTION=="add", ATTR{address}=="38:ea:a7:10:40:ee", NAME="eth4"
SUBSYSTEM=="net", ACTION=="add", ATTR{address}=="38:ea:a7:10:40:ef", NAME="eth5"
""".split('\n')))


def test_udev(dev_list):
    """
    >>> test_udev(dev16_dev_list) == dev16_result
    True
    """
    udev_list = []
    for dev in dev_list:
        udev_list += [udev_str(dev[0], dev[1])]
    return '\n'.join(udev_list)


def create_rule(node):
    udev_list = []
    if hasattr(node, 'ifaces'):
        for iface in node.ifaces:
            if 'mac' in iface:
                ifname = iface['name'] if 'name' in iface else iface['con_name'] if 'con_name' in iface else False
                if ifname:
                    udev_list += [udev_str(ifname, iface['mac'])]

    @session_wrap.sudo
    def func(session):
        if len(udev_list) > 0:
            f_path = '/etc/udev/rules.d/70-persistent-net.rules'
            base_shell.here_doc(session, f_path, udev_list)
    return func
