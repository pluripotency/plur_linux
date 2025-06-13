#! /usr/bin/env python
import os
import sys
sys.path.append(os.pardir)

from plur import base_shell
import re


def add_bond_br(session, br_name, bond_name, ifaces, lacp=True):
    actions = [
        'ovs-vsctl add-bond %s %s %s' % (br_name, bond_name, ' '.join(ifaces))
    ]
    if lacp: actions += ['ovs-vsctl set port %s lacp=active' % bond_name]
    [base_shell.run(session, action) for action in actions]


def show_bond(session, bond_name, lacp=True):
    if lacp:
        action = 'ovs-appctl lacp/show ' + bond_name
    else:
        action = 'ovs-appctl bond/show ' + bond_name
    base_shell.run(session, action)


def add_br(session, br, parent_br=None, vlan_id=None):
    if parent_br:
        action = 'ovs-vsctl add-br %s %s %s' % (br, parent_br, vlan_id)
    else:
        action = 'ovs-vsctl add-br %s' % br
    base_shell.run(session, action)


def del_br(session, br):
    action = 'ovs-vsctl del-br %s ' % br
    base_shell.run(session, action)


def add_port(session, br, port):
    action = 'ovs-vsctl add-port %s %s' % (br, port)
    base_shell.run(session, action)


def del_port(session, port):
    action = 'ovs-vsctl del-port %s' % port
    base_shell.run(session, action)


def configure(session, node):
    if hasattr(node, 'ovsinfo'):
        if not base_shell.check_command_exists(session, 'ovs-vsctl'):
            from plur_linux.recipes.centos.open_vswitch import install
            install.from_openstack(session)
        ovsconf(session, node.ovsinfo)
        if base_shell.check_command_exists(session, 'virsh'):
            destroy_virbr0(session)


def destroy_virbr0(session):
    actions = [
        'ifconfig virbr0 0.0.0.0 down'
        , 'virsh net-autostart default --disable'
        , 'virsh net-destroy default'
    ]
    [base_shell.run(session, action) for action in actions]


def create_sub_br(parent_br, vlan):
    """
    >>> create_sub_br('br0', 100)
    'br0.0100'
    >>> create_sub_br('br0', '100')
    'br0.0100'
    """
    return parent_br + '.' + ('000' + str(vlan))[-4:]


def ovsconf(session, ovsinfo):
    for br in ovsinfo:
        parent_br = br['BRIDGE']
        add_br(session, parent_br)
        if 'VLAN' in br:
            for i, vlan_id in enumerate(br['VLAN']):
                sub_br = create_sub_br(parent_br, vlan_id)
                add_br(session, sub_br, parent_br, vlan_id)
                if 'IP' in br:
                    if br['IP'][i]:
                        base_shell.run(session, 'ifconfig %s %s' % (sub_br, br['IP'][i]))
        if 'BOND' in br:
            bond_name = br['BOND']['NAME']
            slaves = br['BOND']['SLAVES']
            lacp = True if 'LACP' in br['BOND'] and br['BOND']['LACP'] else False
            add_bond_br(session, parent_br, bond_name, slaves, lacp)

        elif 'INTERFACE' in br:
            for inter in br['INTERFACE']:
                add_port(session, parent_br, inter)
                base_shell.run(session, 'ifconfig %s %s' % (inter, 'up'))


def ovsunconf(session, ovsinfo, rm_parent=False):
    for br in ovsinfo:
        parent_br = br['BRIDGE']
        if 'INTERFACE' in br:
            for inter in br['INTERFACE']:
                del_port(session, inter)
                base_shell.run(session, 'ifconfig %s %s' % (inter, 'down'))
        if 'VLAN' in br:
            for i, vlan_id in enumerate(br['VLAN']):
                sub_br = create_sub_br(parent_br, vlan_id)
                if 'IP' in br:
                    if br['IP'][i]:
                        base_shell.run(session, 'ifconfig %s 0.0.0.0 down' % sub_br)
                del_br(session, sub_br)
        if rm_parent:
            del_br(session, parent_br)


capture_example = """
[root@r5 ~]# ./ovsinfo2.py | grep dhguest
[root@r5 ~]#  br2.0127 52:54:00:ff:00:25  vnet6  dhguest
br2.0099 52:54:00:ff:00:c0  vnet7  dhguest
[root@r5 ~]#
"""


def filter_bridge(capture):
    """
    >>> filter_bridge(capture_example)
    ['br2.0127', 'br2.0099']
    """
    return re.findall('br\d\.\d{4}', capture)


def filter_excluded_vlans(bridges, excluded_vlans):
    """
    >>> filter_excluded_vlans(['br2.4084', 'br2.0300'], ['v4084', 'v0002'])
    ['v0300']
    """
    vlans = map(lambda br: 'v' + br.split('.')[1], bridges)
    return filter(lambda vlan: vlan not in excluded_vlans, vlans)


def get_guest_bridges(session, guest_name):
    action = "/root/ovsinfo2.py | grep %s" % guest_name
    capture = session.do(base_shell.create_capture_sequence(action))
    return filter_bridge(capture)


def extract_ovs_con(capture):
    lines = re.split('\r\n|\n', capture)
    print(lines)
    filtered = map(lambda line: line.strip(), filter(lambda line: re.match('.?br.+', line), lines))
    print(filtered)

    def ext(line):
        sp = re.split('\t+|\s+', line)
        return {
            'br': sp[0],
            'mac': sp[1],
            'vnet': sp[2],
            'guest_name': sp[3]
        }
    return map(ext, filtered)


def ovsinfo2(session, guest_name):
    action = "/root/ovsinfo2.py | grep %s" % guest_name
    capture = base_shell.run(session, action)
    return extract_ovs_con(capture)


def move_vnet(session, vnet, dst_br):
    base_shell.run(session, 'ovs-vsctl del-port %s' % vnet)
    base_shell.run(session, 'ovs-vsctl add-port %s %s' % (dst_br, vnet))
