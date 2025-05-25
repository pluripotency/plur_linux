import re
from plur import ansi_colors
from recipes import ipv4
from lib import misc

ex_list_standard_switch = """
esxcli network vswitch standard list
vSwitch0
   Name: vSwitch0
   Class: cswitch
   Num Ports: 3246
   Used Ports: 4
   Configured Ports: 128
   MTU: 1500
   CDP Status: listen
   Beacon Enabled: false
   Beacon Interval: 1
   Beacon Threshold: 3
   Beacon Required By: 
   Uplinks: vmnic0
   Portgroups: VM Network, Management Network

switch01
   Name: switch01
   Class: cswitch
   Num Ports: 3246
   Used Ports: 6
   Configured Ports: 1024
   MTU: 1500
   CDP Status: listen
   Beacon Enabled: false
   Beacon Interval: 1
   Beacon Threshold: 3
   Beacon Required By: 
   Uplinks: vmnic2
   Portgroups: v0003, v0002, v4084
[root@localhost:~] 
"""


def parse_list_standard_switch(output):
    """
    >>> parse_list_standard_switch(ex_list_standard_switch)
    [{'vswitch_name': 'vSwitch0', 'vmnic_list': ['vmnic0'], 'portgroup_list': ['VM Network', 'Management Network']}, {'vswitch_name': 'switch01', 'vmnic_list': ['vmnic2'], 'portgroup_list': ['v0003', 'v0002', 'v4084']}]

    """
    vswitch_name = None
    vmnic_list = None
    portgroup_list = None

    conf_list = []
    if isinstance(output, str) and len(output) > 1:
        for line in re.split('\r\n|\n', output):
            if line.startswith('   '):
                if re.search('^   Name: ', line):
                    vswitch_name = line.split('Name: ')[1].strip()
                elif re.search('^   Uplinks: ', line):
                    uplinks = line.split('Uplinks: ')[1].strip()
                    vmnic_list = re.split(', ', uplinks)
                elif re.search('^   Portgroups: ', line):
                    portgroups = line.split('Portgroups: ')[1].strip()
                    portgroup_list = re.split(', ', portgroups)
            elif vswitch_name:
                obj = {
                    'vswitch_name': vswitch_name
                }
                if vmnic_list:
                    obj['vmnic_list'] = vmnic_list
                if portgroup_list:
                    obj['portgroup_list'] = portgroup_list
                conf_list.append(obj)

                vswitch_name = None
                vmnic_list = None
                portgroup_list = None

    return conf_list


ex_list_portgroup = """
esxcli network vswitch standard portgroup list
Name                Virtual Switch  Active Clients  VLAN ID
------------------  --------------  --------------  -------
Management Network  vSwitch0                     1        0
VM Network          vSwitch0                     0        0
v0002-m             mgmt-sw                      0        2
v0003-svc1-sw2      svc1-sw2                     0        3
v0003-svc2ha        svc2ha-sw                    0        3
v0006-svc2ha        svc2ha-sw                    0        6
v0305-m             mgmt-sw                      0      305
[root@localhost:~]
"""


def parse_list_portgroup(output):
    """
    >>> parse_list_portgroup(ex_list_portgroup)
    [{'portgroup': 'Management Network', 'vswitch_name': 'Switch0', 'active_clients': '1', 'vlan_id': '0'}, {'portgroup': 'VM Network', 'vswitch_name': 'Switch0', 'active_clients': '0', 'vlan_id': '0'}, {'portgroup': 'v0002-m', 'vswitch_name': 'gmt-sw', 'active_clients': '0', 'vlan_id': '2'}, {'portgroup': 'v0003-svc1-sw2', 'vswitch_name': 'vc1-sw2', 'active_clients': '0', 'vlan_id': '3'}, {'portgroup': 'v0003-svc2ha', 'vswitch_name': 'vc2ha-sw', 'active_clients': '0', 'vlan_id': '3'}, {'portgroup': 'v0006-svc2ha', 'vswitch_name': 'vc2ha-sw', 'active_clients': '0', 'vlan_id': '6'}, {'portgroup': 'v0305-m', 'vswitch_name': 'gmt-sw', 'active_clients': '0', 'vlan_id': '305'}]

    """
    conf_list = []
    if isinstance(output, str) and len(output) > 1:
        for line in re.split('\r\n|\n', output):
            if len(line) == 59 and re.search('\d', line[58]):
                obj = {
                    'portgroup': line[:19].strip(),
                    'vswitch_name': line[21:35].strip(),
                    'active_clients': line[37:51].strip(),
                    'vlan_id': line[53:59].strip(),
                }
                conf_list.append(obj)

    return conf_list


ex_list_vmnic = """
esxcli network nic list
Name     PCI Device    Driver  Admin Status  Link Status  Speed  Duplex  MAC Address         MTU  Description
-------  ------------  ------  ------------  -----------  -----  ------  -----------------  ----  -------------------------------------------------------
vmnic0   0000:c1:00.0  ntg3    Up            Up            1000  Full    2c:ea:7f:f2:2f:48  1500  Broadcom Corporation NetXtreme BCM5720 Gigabit Ethernet
vmnic1   0000:c1:00.1  ntg3    Up            Down             0  Half    2c:ea:7f:f2:2f:49  1500  Broadcom Corporation NetXtreme BCM5720 Gigabit Ethernet
vmnic10  0000:41:00.2  ntg3    Up            Up            1000  Full    b0:26:28:9c:f8:2e  1500  Broadcom Corporation NetXtreme BCM5719 Gigabit Ethernet
vmnic11  0000:41:00.3  ntg3    Up            Down             0  Half    b0:26:28:9c:f8:2f  1500  Broadcom Corporation NetXtreme BCM5719 Gigabit Ethernet
vmnic2   0000:02:00.0  ntg3    Up            Up            1000  Full    2c:ea:7f:64:8d:3e  1500  Broadcom Corporation NetXtreme BCM5720 Gigabit Ethernet
vmnic3   0000:02:00.1  ntg3    Up            Down             0  Half    2c:ea:7f:64:8d:3f  1500  Broadcom Corporation NetXtreme BCM5720 Gigabit Ethernet
vmnic4   0000:c4:00.0  ntg3    Up            Up            1000  Full    b0:26:28:9c:f8:34  1500  Broadcom Corporation NetXtreme BCM5719 Gigabit Ethernet
vmnic5   0000:c4:00.1  ntg3    Up            Up            1000  Full    b0:26:28:9c:f8:35  1500  Broadcom Corporation NetXtreme BCM5719 Gigabit Ethernet
vmnic6   0000:c4:00.2  ntg3    Up            Up            1000  Full    b0:26:28:9c:f8:36  1500  Broadcom Corporation NetXtreme BCM5719 Gigabit Ethernet
vmnic7   0000:c4:00.3  ntg3    Up            Down             0  Half    b0:26:28:9c:f8:37  1500  Broadcom Corporation NetXtreme BCM5719 Gigabit Ethernet
vmnic8   0000:41:00.0  ntg3    Up            Up            1000  Full    b0:26:28:9c:f8:2c  1500  Broadcom Corporation NetXtreme BCM5719 Gigabit Ethernet
vmnic9   0000:41:00.1  ntg3    Up            Up            1000  Full    b0:26:28:9c:f8:2d  1500  Broadcom Corporation NetXtreme BCM5719 Gigabit Ethernet
[root@localhost:~] 
"""
ex2_list_vmnic = """
esxcli network nic list
Name    PCI Device    Driver  Admin Status  Link Status  Speed  Duplex  MAC Address         MTU  Description
------  ------------  ------  ------------  -----------  -----  ------  -----------------  ----  -------------------------------------------------------
vmnic0  0000:c1:00.0  ntg3    Up            Up            1000  Full    2c:ea:7f:f2:2f:48  1500  Broadcom Corporation NetXtreme BCM5720 Gigabit Ethernet
[root@localhost:~] 
"""


def parse_list_vmnic(output):
    """
    >>> parse_list_vmnic(ex_list_vmnic)
    [{'vmnic': 'vmnic0', 'link_status': 'Up', 'speed': '1000/Full'}, {'vmnic': 'vmnic1', 'link_status': 'Down', 'speed': '0/Half'}, {'vmnic': 'vmnic10', 'link_status': 'Up', 'speed': '1000/Full'}, {'vmnic': 'vmnic11', 'link_status': 'Down', 'speed': '0/Half'}, {'vmnic': 'vmnic2', 'link_status': 'Up', 'speed': '1000/Full'}, {'vmnic': 'vmnic3', 'link_status': 'Down', 'speed': '0/Half'}, {'vmnic': 'vmnic4', 'link_status': 'Up', 'speed': '1000/Full'}, {'vmnic': 'vmnic5', 'link_status': 'Up', 'speed': '1000/Full'}, {'vmnic': 'vmnic6', 'link_status': 'Up', 'speed': '1000/Full'}, {'vmnic': 'vmnic7', 'link_status': 'Down', 'speed': '0/Half'}, {'vmnic': 'vmnic8', 'link_status': 'Up', 'speed': '1000/Full'}, {'vmnic': 'vmnic9', 'link_status': 'Up', 'speed': '1000/Full'}]
    >>> parse_list_vmnic(ex2_list_vmnic)
    [{'vmnic': 'vmnic0', 'link_status': 'Up', 'speed': '1000/Full'}]

    """
    conf_list = []
    if isinstance(output, str) and len(output) > 1:
        sp_type = 9
        for line in re.split('\r\n|\n', output):
            if len(line) > 100 and line[10:13] == 'PCI':
                sp_type = 10
            if len(line) > 100 and re.search('\d', line[10]):
                obj = {
                    'vmnic': line[:8].strip(),
                    'link_status': line[35+sp_type:47+sp_type].strip(),
                    'speed': line[48+sp_type:54+sp_type].strip() + '/' + line[55+sp_type:62+sp_type].strip(),
                }
                conf_list.append(obj)

    return conf_list


ex_list_ip_interface = """
esxcli network ip interface list
vmk0
   Name: vmk0
   MAC Address: 52:54:00:ad:48:01
   Enabled: true
   Portset: vSwitch0
   Portgroup: v4084unt-k
   Netstack Instance: defaultTcpipStack
   VDS Name: N/A
   VDS UUID: N/A
   VDS Port: N/A
   VDS Connection: -1
   Opaque Network ID: N/A
   Opaque Network Type: N/A
   External ID: N/A
   MTU: 1500
   TSO MSS: 65535
   RXDispQueue Size: 1
   Port ID: 33554436

vmk1
   Name: vmk1
   MAC Address: 00:50:56:60:e9:fc
   Enabled: true
   Portset: mgmt-sw
   Portgroup: v0002-m
   Netstack Instance: defaultTcpipStack
   VDS Name: N/A
   VDS UUID: N/A
   VDS Port: N/A
   VDS Connection: -1
   Opaque Network ID: N/A
   Opaque Network Type: N/A
   External ID: N/A
   MTU: 1500
   TSO MSS: 65535
   RXDispQueue Size: 1
   Port ID: 100687874
"""


def parse_list_ip_interface(output):
    """
    >>> parse_list_ip_interface(ex_list_ip_interface)
    [{'vmk_name': 'vmk0', 'vswitch_name': 'vSwitch0', 'portgroup': 'v4084unt-k'}, {'vmk_name': 'vmk1', 'vswitch_name': 'mgmt-sw', 'portgroup': 'v0002-m'}]
    """
    vmk_name = None
    vswitch_name = None
    portgroup_name = None

    conf_list = []
    if isinstance(output, str) and len(output) > 1:
        for line in re.split('\r\n|\n', output):
            if line.startswith('   '):
                if re.search('^   Name: ', line):
                    vmk_name = line.split('Name: ')[1].strip()
                elif re.search('^   Portset: ', line):
                    vswitch_name = line.split('Portset: ')[1].strip()
                elif re.search('^   Portgroup: ', line):
                    portgroup_name = line.split('Portgroup: ')[1].strip()
            elif vmk_name:
                obj = {
                    'vmk_name': vmk_name
                }
                if vswitch_name:
                    obj['vswitch_name'] = vswitch_name
                if portgroup_name:
                    obj['portgroup'] = portgroup_name
                conf_list.append(obj)
                vmk_name = None
                vswitch_name = None
                portgroup_name = None


    return conf_list


ex_vmk_ip_list = """
esxcli network ip interface ipv4 get
Name  IPv4 Address   IPv4 Netmask   IPv4 Broadcast  Address Type  Gateway        DHCP DNS
----  -------------  -------------  --------------  ------------  -------------  --------
vmk0  192.168.10.67  255.255.255.0  192.168.10.255  STATIC        192.168.10.62     false
vmk1  172.25.3.67    255.255.252.0  172.25.3.255    STATIC        0.0.0.0           false
"""


def parse_list_vmk_ip(output):
    """
    >>> parse_list_vmk_ip(ex_vmk_ip_list)
    [{'vmk_name': 'vmk0', 'ip': '192.168.10.67/24'}, {'vmk_name': 'vmk1', 'ip': '172.25.3.67/22'}]
    """
    conf_list = []
    if isinstance(output, str) and len(output) > 1:
        for line in re.split('\r\n|\n', output):
            if line.startswith('vmk'):
                sp = re.split('\s+', line)
                vmk_name = sp[0]
                vmk_ipv4 = sp[1]
                vmk_netmask = sp[2]
                obj = {
                    'vmk_name': vmk_name
                    , 'ip': f'{vmk_ipv4}/{ipv4.netmask_to_prefix(vmk_netmask)}'
                }
                conf_list.append(obj)

    return conf_list


def parse_vswitch_obj_portgroup(portgroup_line):
    """
    >>> parse_vswitch_obj_portgroup("v0002-k vid:2 vmk1:172.25.2.161/22")
    ['v0002-k', '2', '172.25.2.161/22']
    """
    sp = portgroup_line.split(' ')
    portgroup = sp[0]
    vid_pos = sp[1]
    if vid_pos.startswith('vid:'):
        vid = vid_pos.split(':')[1]
    else:
        print(ansi_colors.red(f'invalid vid param: {portgroup_line}'))
        exit(1)
    if len(sp) > 2:
        vmk_pos = sp[2]
        ssp = vmk_pos.split(':')
        vmk = {
            'name': ssp[0]
            , 'ip': ssp[1]
        }
    else:
        vmk = None
    return [
        portgroup
        , vid
        , vmk
    ]


def find_attr(attr, value_list, value):
    return misc.find(value_list, lambda x: x[attr] == value)


def find_vmnic(list_vmnic, vmnic_name):
    return find_attr('vmnic', list_vmnic, vmnic_name)


def find_portgroup(list_portgroup, portgroup_name):
    return find_attr('portgroup', list_portgroup, portgroup_name)


def summary_parsed(list_switch, list_portgroup, list_vmnic, list_ip_interface, list_vmk_ip):
    translated = []
    for switch in list_switch:
        obj = {
            'vswitch_name': switch['vswitch_name']
        }
        if 'portgroup_list' in switch:
            portgroup_list = switch['portgroup_list']
            for i, portgroup_name in enumerate(portgroup_list):
                found = find_portgroup(list_portgroup, portgroup_name)
                if found:
                    portgroup_summary = f'{portgroup_name} vid:{found["vlan_id"]}'
                    found_vmk = find_attr('portgroup', list_ip_interface, portgroup_name)
                    if found_vmk:
                        vmk_name = found_vmk['vmk_name']
                        found_vmk_ip = find_attr('vmk_name', list_vmk_ip, vmk_name)
                        if found_vmk_ip:
                            vmk_ip = found_vmk_ip['ip']
                            portgroup_summary += f' {vmk_name}:{vmk_ip}'
                    portgroup_list[i] = portgroup_summary
            obj['portgroup_list'] = portgroup_list
        if 'vmnic_list' in switch:
            vmnic_list = switch['vmnic_list']
            for i, vmnic in enumerate(vmnic_list):
                found = find_vmnic(list_vmnic, vmnic)
                if found:
                    vmnic_list[i] = f'{vmnic} {found["link_status"]} {found["speed"]}'
            obj['vmnic_list'] = vmnic_list
        translated += [obj]
    return translated


