from . import nmcli_str


def add(con_name, type='ovs-bridge', ifname=None, options=''):
    ifname = con_name if ifname is None else ifname
    return f"nmcli con add type {type} con-name {con_name} c.interface {ifname} {options}"


def con_add_br(bridge_name, phy_dev_name=None, ipv4_params=None):
    br_port = bridge_name + '_port'
    br_int = bridge_name + '_interface'
    cmds = [
        add(bridge_name)
        , add(br_port, type='ovs-port', ifname=bridge_name, options=f'master {bridge_name}')
        , add(br_int, type='ovs-interface', ifname=bridge_name, options=f'slave-type ovs-port master {br_port}')
        , nmcli_str.mod_ip(br_int, **ipv4_params)
    ]
    if phy_dev_name:
        br_phy_port = bridge_name + f'_{phy_dev_name}'
        cmds += [
            add(br_phy_port, type='ovs-port', ifname=br_phy_port, options=f'master {bridge_name}')
            , add(phy_dev_name, type='ethernet', ifname=phy_dev_name, options=f'master {br_port}')
        ]


not_supported = """
# no way to set ip to br2.4084 by nmcli
# use /etc/sysconfig/network-scripts/ifcfg-br2.4084
TYPE=OVSBridge
BOOTPROTO=none
IPADDR=192.168.10.15
PREFIX=24
IPV4_FAILURE_FATAL=no
IPV6_DISABLED=yes
IPV6INIT=no
DEVICE=br2.4084
ONBOOT=yes
NM_CONTROLLED=no
"""

ex_about_nmcli_ovs = """
# needed
dnf install NetworkManager-ovs
systemctl restart NetworkManager


https://developer-old.gnome.org/NetworkManager/stable/nm-openvswitch.html
ovs-vsctl show
da9f3757-de28-482c-9e3c-7716edad92ab
    Bridge br0
        Port br0
            Interface br0
                type: internal
        Port enp2s0
            Interface enp2s0
                type: system
    ovs_version: "2.17.6"
    
nmcli c
iface0   a0f2697f-8bc2-4d1d-b297-7bb80c885f31  ovs-interface  br0     
br0      e8fc84a7-3713-48de-9dbc-1c2d8696c191  ovs-bridge     br0     
enp2s0   ff89fb54-73f5-41f7-a814-0adf4ed24e13  ethernet       enp2s0  
port0    3b0c82d6-a150-4d2c-a00f-a61d3facaf16  ovs-port       br0     
port1    c110272e-0645-40b3-b4f4-3849f1b4ad3e  ovs-port       enp2s0  
"""

ex_ovs = """
#! /bin/sh
BRIDGE=br0
PORT1=port1
PHY=enp2s0
PORT0=port0
IFACE0=iface0
IP=192.168.0.71/24
GW=192.168.0.1
DNS=8.8.8.8,8.8.4.4

sudo nmcli con del $BRIDGE
sudo nmcli con del $PORT0
sudo nmcli con del $IFACE0
sudo nmcli con del $PORT1
sudo nmcli con del $PHY

sudo nmcli con add type ovs-bridge con-name $BRIDGE con.interface $BRIDGE
sudo nmcli con add type ovs-port con-name $PORT0 con.interface $BRIDGE master $BRIDGE
sudo nmcli con add type ovs-interface slave-type ovs-port con-name $IFACE0 con.interface $BRIDGE master $PORT0
sudo nmcli con mod $IFACE0 ipv6.method ignore ipv4.method manual ipv4.address $IP ipv4.gateway $GW ipv4.dns $DNS
sudo nmcli con add type ovs-port con-name $PORT1 con.interface $PHY master $BRIDGE
sudo nmcli con add type ethernet con-name $PHY con.interface $PHY master $PORT1

sudo nmcli con up $BRIDGE
sudo nmcli con up $PORT0
sudo nmcli con up $IFACE0
sudo nmcli con up $PORT1
sudo nmcli con up $PHY
"""

ex_ovs_vlan = """
#! /bin/sh
BRIDGE=br0
PORT1=port1
PHY=enp2s0
PORT0=port0
IFACE0=iface0
IP=192.168.0.71/24
GW=192.168.0.1
DNS=8.8.8.8,8.8.4.4

VLAN1_PORT=v3000
VLAN1_INT=v3000int
VLAN1_TAG=3000
VLAN1_IP=10.30.0.81/24

sudo nmcli con del $VLAN1_INT
sudo nmcli con del $VLAN1_PORT

sudo nmcli con del $BRIDGE
sudo nmcli con del $PORT0
sudo nmcli con del $IFACE0
sudo nmcli con del $PORT1
sudo nmcli con del $PHY

sudo nmcli con add type ovs-bridge con-name $BRIDGE con.interface $BRIDGE
sudo nmcli con add type ovs-port con-name $PORT0 con.interface $BRIDGE master $BRIDGE
sudo nmcli con add type ovs-interface slave-type ovs-port con-name $IFACE0 con.interface $BRIDGE master $PORT0
sudo nmcli con mod $IFACE0 ipv6.method ignore ipv4.method manual ipv4.address $IP ipv4.gateway $GW ipv4.dns $DNS
sudo nmcli con add type ovs-port con-name $PORT1 con.interface $PHY master $BRIDGE
sudo nmcli con add type ethernet con-name $PHY con.interface $PHY master $PORT1

sudo nmcli con add type ovs-port con-name $VLAN1_PORT con.interface vlan$VLAN1_TAG master $BRIDGE ovs-port.tag $VLAN1_TAG con-name $VLAN1_PORT
sudo nmcli con add type ovs-interface slave-type ovs-port con.interface vlan$VLAN1_TAG master $VLAN1_PORT con-name $VLAN1_INT
sudo nmcli con mod $VLAN1_INT ipv6.method ignore ipv4.method manual ipv4.address $VLAN1_IP

sudo nmcli con up $BRIDGE
sudo nmcli con up $PORT0
sudo nmcli con up $IFACE0
sudo nmcli con up $PORT1
sudo nmcli con up $PHY

sudo nmcli con up $VLAN1_PORT
sudo nmcli con up $VLAN1_INT
"""
