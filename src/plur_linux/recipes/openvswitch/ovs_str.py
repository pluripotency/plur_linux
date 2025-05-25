def add_bond_br_str(br_name, bond_name, iface_list, bond_option='lacp=active'):
    actions = [
        f'ovs-vsctl add-bond {br_name} {bond_name} {" ".join(iface_list)}'
    ]
    if bond_option:
        actions += [f'ovs-vsctl set port {bond_name} {bond_option}']
    return actions


def show_bond_str(bond_name, lacp=True):
    if lacp:
        return 'ovs-appctl lacp/show ' + bond_name
    else:
        return 'ovs-appctl bond/show ' + bond_name


def add_br_str(br, parent_br=None, vlan_id=None):
    if parent_br and vlan_id:
        return f'ovs-vsctl add-br {br} {parent_br} {vlan_id}'
    else:
        return 'ovs-vsctl add-br ' + br


def del_br_str(br):
    return 'ovs-vsctl del-br  ' + br


def add_port(br, port):
    return f'ovs-vsctl add-port {br} {port}'


def del_port(port):
    return 'ovs-vsctl del-port ' + port


ex_add_bond_with_nm_iface_sh = """
#! /bin/bash

BRIDGE_NAME=br2
BOND_NAME=bond2
IFACES="ens1f2 eno7"
declare -a VID_LIST=("699" "1002" "3000" "4084" "2")

#ovs-vsctl del-br br2

ovs-vsctl add-br ${BRIDGE_NAME}
ovs-vsctl add-bond ${BRIDGE_NAME} ${BOND_NAME} ${IFACES}
ovs-vsctl set port ${BOND_NAME} lacp=active

ovs-appctl lacp/show

for VID in ${VID_LIST[@]};do
  DIGI4=$(printf "%04d" "${VID}")
  SUBBR=${BRIDGE_NAME}.${DIGI4}
  ovs-vsctl add-br ${SUBBR} ${BRIDGE_NAME} ${VID}
  ip l set up dev ${SUBBR}
done
"""