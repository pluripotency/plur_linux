from plur import base_shell


def remove_current_ifcfg(session):
    base_shell.work_on(session, '/etc/sysconfig/network-scripts')
    not_remove = [
        'lo'
    ]
    # for iface in ifaces:
    #     dev_name = iface['name'] if 'name' in iface else iface['con_name'] if 'con_name' in iface else None
    #     not_remove += [
    #         dev_name
    #     ]
    not_remove_str = ' '.join([f' | grep -v ifcfg-{dev_name}' for dev_name in not_remove])
    remove_command = f'ls ifcfg-* {not_remove_str}| xargs rm -f'
    base_shell.run(session, remove_command)


def configure(iface):
    """
    ifaces_example = [
        {
            'name': 'bond1', 'ip': '192.168.0.1/24', 'up': True,
            'bond_params': 'miimon=100 mode=active-backup downdelay=200 updelay=200'
        },
        {
            'name': 'bond2', 'ip': None, 'up': True,
            'bond_params': 'miimon=100 mode=4 downdelay=200 updelay=200'
        },
        {'name': 'eth0', 'ip': None, 'up': True, 'lldp': True, 'slave_of': 'bond1'},
        {'name': 'eth1', 'ip': None, 'up': True, 'lldp': True, 'slave_of': 'bond1'},
        {'name': 'eth2', 'ip': None, 'up': True, 'lldp': True, 'slave_of': 'bond2'},
        {'name': 'eth3', 'ip': None, 'up': True, 'lldp': True, 'slave_of': 'bond2'},
    ]
    c7_ifaces = [{
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
        dev_name = iface['name'] if 'name' in iface else iface['con_name'] if 'con_name' in iface else None
        if dev_name:
            contents = [
                'DEVICE="%s"' % dev_name,
                'NM_CONTROLLED="no"',
                'IPV6INIT="no"'
            ]
            on_boot = iface['autoconnect'] if 'autoconnect' in iface else iface['up'] if 'up' in iface else False
            contents += ['ONBOOT="%s"' % ('yes' if on_boot else 'no')]

            hwaddr = iface['hwaddr'] if 'hwaddr' in iface else iface['mac'] if 'mac' in iface else False
            if hwaddr:
                contents += ['HWADDR="%s"' % hwaddr]

            if 'ip' in iface:
                if iface['ip'] == 'dhcp':
                    contents += ['BOOTPROTO="dhcp"']
                elif iface['ip'] is None:
                    contents += ['BOOTPROTO="none"']
                else:
                    ipaddr = iface['ip'].split('/')
                    contents += ['BOOTPROTO="static"', 'IPADDR="%s"' % ipaddr[0], 'PREFIX="%s"' % ipaddr[1]]
            else:
                contents += ['BOOTPROTO="none"']

            if 'gateway' in iface:
                contents += ['GATEWAY="%s"' % iface['gateway']]

            if 'search' in iface:
                contents += [f'DOMAIN="{iface["search"]}"']

            if 'nameservers' in iface:
                for i, dns in enumerate(iface['nameservers']):
                    contents += ['DNS%s="%s"' % ((i+1), dns)]

            if 'slave_of' in iface:
                contents += ['MASTER="%s"' % iface['slave_of'], 'SLAVE="yes"']

            if 'bond_params' in iface:
                contents += ['BONDING_OPTS="%s"' % iface['bond_params']]

            if 'options' in iface:
                contents += iface['options']

            if 'mtu' in iface:
                contents += ['MTU="%s"' % iface['mtu']]

            ifcfg_file = '/etc/sysconfig/network-scripts/ifcfg-%s' % dev_name
            base_shell.here_doc(session, ifcfg_file, contents)

            if 'routes' in iface:
                if isinstance(iface['routes'], list) and len(iface['routes']) > 0:
                    route_file = '/etc/sysconfig/network-scripts/route-%s' % dev_name
                    routes = []
                    for route in iface['routes']:
                        sp = route.split(' ')
                        routes += [sp[0] + ' via ' + sp[1] + ' dev %s' % dev_name]
                    base_shell.here_doc(session, route_file, routes)
    return func



