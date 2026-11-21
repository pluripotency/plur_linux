from mini import misc

ex_bond_bridge = """
nmcli con add type bond con-name bond0 ifname bond0 mode 802.3ad autoconnect yes
nmcli con mod bond0 ipv4.method disabled ipv6.method ignore

nmcli con add type bond-slave con-name em1 ifname em1 master bond0 autoconnect yes
nmcli con add type bond-slave con-name em2 ifname em2 master bond0 autoconnect yes

nmcli con add type bridge con-name br0 ifname br0 autoconnect yes
nmcli con mod br0 bridge.stp no
nmcli con mod br0 ipv4.method disabled ipv6.method ignore
nmcli con up br0

nmcli con mod bond0 connection.master br0 connection.slave-type bridge
"""

ex_bond_bridge_vlan = ex_bond_bridge + """
nmcli con add type bridge con-name br0.4084 ifname br0.4084 autoconnect yes
nmcli con mod br0.4084 bridge.stp no
nmcli con mod br0.4084 ipv4.method disabled ipv6.method ignore
nmcli con up br0.4084

nmcli con add type vlan con-name bond0.4084 ifname bond0.4084 dev bond0 id 4084
nmcli con mod bond0.4084 connection.master br0.4084 connection.slave-type bridge
nmcli con up bond0.4084
"""

ex_bond_bridge_vlan_sh = """
#! /bin/sh
BRIDGE_NAME=br2
BOND_NAME=bond2
declare -a IFACE_LIST=("ens1f2" "eno7")
declare -a VID_LIST=("4084" "2")

for VID in ${VID_LIST[@]};do
  DIGI4=$(printf "%04d" "${VID}")
  SUBBR=${BRIDGE_NAME}.${DIGI4}
  SUBBOND=${BOND_NAME}.${DIGI4}
  nmcli con del ${SUBBR}
  nmcli con del ${SUBBOND}
done
for IFACE in ${IFACE_LIST[@]};do
  nmcli con del ${IFACE}
done
nmcli con del ${BOND_NAME}
nmcli con del ${BRIDGE_NAME}
nmcli con del "Wired connection 1"


nmcli con add type bond con-name ${BOND_NAME} ifname ${BOND_NAME} mode 802.3ad autoconnect yes
nmcli con mod ${BOND_NAME} ipv4.method disabled ipv6.method ignore

for IFACE in ${IFACE_LIST[@]};do
  nmcli con add type bond-slave con-name ${IFACE} ifname ${IFACE} master ${BOND_NAME} autoconnect yes
done
nmcli con up ${BOND_NAME}

nmcli con add type bridge con-name ${BRIDGE_NAME} ifname ${BRIDGE_NAME} autoconnect yes
nmcli con mod ${BRIDGE_NAME} bridge.stp no
nmcli con mod ${BRIDGE_NAME} ipv4.method disabled ipv6.method ignore
nmcli con up ${BRIDGE_NAME}

nmcli con mod ${BOND_NAME} connection.master ${BRIDGE_NAME} connection.slave-type bridge

for VID in ${VID_LIST[@]};do
  DIGI4=$(printf "%04d" "${VID}")
  SUBBR=${BRIDGE_NAME}.${DIGI4}
  SUBBOND=${BOND_NAME}.${DIGI4}
  nmcli con add type bridge con-name ${SUBBR} ifname ${SUBBR} autoconnect yes
  nmcli con mod ${SUBBR} bridge.stp no
  nmcli con mod ${SUBBR} ipv4.method disabled ipv6.method ignore
  nmcli con up  ${SUBBR}
  nmcli con add type vlan con-name ${SUBBOND} ifname ${SUBBOND} dev ${BOND_NAME} id ${VID}
  nmcli con mod ${SUBBOND} connection.master ${SUBBR} connection.slave-type bridge
  nmcli con up ${SUBBOND}
done
"""

nmcli_vlan_str = """
#!/bin/sh
IFACE=eth1
VLANID=100

nmcli c add type ethernet con-name $IFACE ifname $IFACE ipv6.method ignore ipv4.method disabled
nmcli con add type vlan ifname $IFACE.$VLANID dev $IFACE id $VLANID
nmcli c up $IFACE
nmcli c up $IFACE.$VLANID

IP=192.168.100.254/24
nmcli c mod $IFACE.$VLANID ipv4.method manual ipv4.address $IP
"""

bonding_mode_choice = [
    'balance-rr'
    , 'active-backup'
    , 'balance-xor'
    , 'broadcast'
    , '802.3ad'
    , 'balance-tlb'
    , 'balance-alb'
]


class BondBridgeVlan:
    def __int__(self, br_name, bond_name, iface_list, vid_list):
        # no ip conf in this class
        self.declare_str = self._declare_contents(br_name, bond_name, iface_list, vid_list)

    def _declare_contents(self, br_name, bond_name, iface_list, vid_list):
        iface_list_str = '"' + '" "'.join(iface_list) + '"'
        vid_list_str = '"' + '" "'.join(vid_list) + '"'
        return misc.del_indent(f"""
        #! /bin/sh
        BRIDGE_NAME={br_name}
        BOND_NAME={bond_name}
        declare -a IFACE_LIST=({iface_list_str})
        declare -a VID_LIST=({vid_list_str})
        """)

    def _delete_contents(self):
        return misc.del_indent("""
        
        for VID in ${VID_LIST[@]};do
          DIGI4=$(printf "%04d" "${VID}")
          SUBBR=${BRIDGE_NAME}.${DIGI4}
          SUBBOND=${BOND_NAME}.${DIGI4}
          nmcli con del ${SUBBR}
          nmcli con del ${SUBBOND}
        done
        for IFACE in ${IFACE_LIST[@]};do
          nmcli con del ${IFACE}
        done
        nmcli con del ${BOND_NAME}
        nmcli con del ${BRIDGE_NAME}
        nmcli con del "Wired connection 1"
        
        """)

    def _create_contents(self):
        return misc.del_indent("""
        
        nmcli con add type bond con-name ${BOND_NAME} ifname ${BOND_NAME} mode 802.3ad autoconnect yes
        nmcli con mod ${BOND_NAME} ipv4.method disabled ipv6.method ignore

        for IFACE in ${IFACE_LIST[@]};do
          nmcli con add type bond-slave con-name ${IFACE} ifname ${IFACE} master ${BOND_NAME} autoconnect yes
        done
        nmcli con up ${BOND_NAME}

        nmcli con add type bridge con-name ${BRIDGE_NAME} ifname ${BRIDGE_NAME} autoconnect yes
        nmcli con mod ${BRIDGE_NAME} bridge.stp no
        nmcli con mod ${BRIDGE_NAME} ipv4.method disabled ipv6.method ignore
        nmcli con up ${BRIDGE_NAME}

        nmcli con mod ${BOND_NAME} connection.master ${BRIDGE_NAME} connection.slave-type bridge

        for VID in ${VID_LIST[@]};do
          DIGI4=$(printf "%04d" "${VID}")
          SUBBR=${BRIDGE_NAME}.${DIGI4}
          SUBBOND=${BOND_NAME}.${DIGI4}
          nmcli con add type bridge con-name ${SUBBR} ifname ${SUBBR} autoconnect yes
          nmcli con mod ${SUBBR} bridge.stp no
          nmcli con mod ${SUBBR} ipv4.method disabled ipv6.method ignore
          nmcli con up  ${SUBBR}
          nmcli con add type vlan con-name ${SUBBOND} ifname ${SUBBOND} dev ${BOND_NAME} id ${VID}
          nmcli con mod ${SUBBOND} connection.master ${SUBBR} connection.slave-type bridge
          nmcli con up ${SUBBOND}
        done
        """)

    def create_sh_str(self):
        return self.declare_str + self._delete_contents() + self._create_contents()

    def delete_sh_str(self):
        return self.declare_str + self._delete_contents()
