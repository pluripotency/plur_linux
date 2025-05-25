
def add_vlan_str(vlan_id, interface, tag=True):
    if tag:
        return f'vlan {vlan_id} tag {interface}'
    else:
        return f'vlan {vlan_id} untag {interface}'


def del_vlan_str(vlan_id, interface, tag=True):
    return f'no {add_vlan_str(vlan_id, interface, tag)}'
