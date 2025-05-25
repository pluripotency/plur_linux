import re


def vswitch_name_option(vswitch_name):
    return f'--vswitch-name="{vswitch_name}"'


def add_vmnic_str(vmnic, vswitch_name):
    return f'esxcli network vswitch standard uplink add --uplink-name={vmnic} {vswitch_name_option(vswitch_name)}'


def remove_vmnic_str(vmnic, vswitch_name):
    return f'esxcli network vswitch standard uplink remove --uplink-name={vmnic} {vswitch_name_option(vswitch_name)}'


def show_vmnic_list_str():
    return 'esxcli network nic list'


def add_standard_vswitch_str(vswitch_name):
    return f'esxcli network vswitch standard add {vswitch_name_option(vswitch_name)}'


def set_starndard_vswitch_policy_security_str(vswitch_name, promiscuous=True, mac_change=True, forged_transmit=True):
    if promiscuous:
        p = 'true'
    else:
        p = 'false'
    if mac_change:
        m = 'true'
    else:
        m = 'false'
    if forged_transmit:
        f = 'true'
    else:
        f = 'false'
    return f'esxcli network vswitch standard policy security set -f {f} -m {m} -p {p} {vswitch_name_option(vswitch_name)}'


def show_standard_vswitch_policy_security_str(vswitch_name):
    return f'esxcli network vswitch standard policy security get {vswitch_name_option(vswitch_name)}'


def remove_standard_vswitch_str(vswitch_name):
    return f'esxcli network vswitch standard remove {vswitch_name_option(vswitch_name)}'


def show_vswitch_standard_list_str():
    return 'esxcli network vswitch standard list'


def add_portgroup_str(portgroup, vswitch_name):
    return f'esxcli network vswitch standard portgroup add --portgroup-name={portgroup} {vswitch_name_option(vswitch_name)}'


def remove_portgroup_str(portgroup, vswitch_name):
    return f'esxcli network vswitch standard portgroup remove --portgroup-name={portgroup} {vswitch_name_option(vswitch_name)}'


def add_vmkernel_to_portgroup_str_list(portgroup, vmk_name, vmk_ip, vmk_netmask):
    return [
        f'esxcli network ip interface add --interface-name={vmk_name} --portgroup-name={portgroup}'
        , f'esxcli network ip interface ipv4 set --interface-name={vmk_name} --ipv4={vmk_ip} --netmask={vmk_netmask} --type=static'
    ]


def remove_vmkernel_str(vmk_name):
    return f'esxcli network ip interface remove --interface-name={vmk_name}'


def show_ip_interface_list_str():
    return 'esxcli network ip interface list'


def show_vmk_ip_list_str():
    return f'esxcli network ip interface ipv4 get'


def show_vmk_ip_str(vmk_name):
    return f'esxcli network ip interface ipv4 get -i {vmk_name}'


def show_portgroup_list_str():
    return f'esxcli network vswitch standard portgroup list'


def set_vid_to_portgroup_str(vid, portgroup):
    return f'esxcli network vswitch standard portgroup set -p {portgroup} --vlan-id {vid}'


def show_vm_list_str():
    return 'esxcli network vm list'


def services_restart_str():
    return f'services.sh restart'


w_summary_json = """
[
  {
    "vswitch_name": "svc1-sw1",
    "portgroup_list": [
      "v0002-svc1-sw1 vid:2",
      "v0003-svc1-sw1 vid:3"
    ],
    "vmnic_list": [
      "vmnic5 Up 1000/Full"
    ]
  },
  {
    "vswitch_name": "svc2ha-sw",
    "portgroup_list": [
      "v0006-svc2ha vid:6",
      "v0002-svc2ha vid:2",
      "v0003-svc2ha vid:3"
    ],
    "vmnic_list": [
      "vmnic10 Up 1000/Full",
      "vmnic6 Up 1000/Full"
    ]
  },
  {
    "vswitch_name": "svc1-sw2",
    "portgroup_list": [
      "v0003-svc1-sw2 vid:3"
    ],
    "vmnic_list": [
      "vmnic9 Up 1000/Full"
    ]
  },
  {
    "vswitch_name": "mgmt-sw",
    "portgroup_list": [
      "v0002-m vid:2"
    ],
    "vmnic_list": [
      "vmnic8 Up 1000/Full",
      "vmnic4 Up 1000/Full"
    ]
  }
]
"""
w_additional = """
[
  {
    "vswitch_name": "vSwitch0",
    "portgroup_list": [
      "v4084unt vid:0",
      "v4084unt-k vid:0 vmk0: 192.168.10.5x"
    ],
    "vmnic_list": [
      "vmnic0 Up 1000/Full"
    ]
  },
  {
    "vswitch_name": "admin-sw",
    "portgroup_list": [
      "v0002 vid:2",
      "v0002-k vid:2 vmk1: 172.25.2.16x"
    ],
    "vmnic_list": [
      "vmnic2 Up 1000/Full"
    ]
  }
]
"""
