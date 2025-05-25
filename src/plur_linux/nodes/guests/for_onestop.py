from nodes import r21_c7

dhdock_list = [
    # hostname,  ip seed
    ['w_zab1', 200],
    ['y_zab1', 200],
    ['t_zab1', 200],
    ['k_zab1', 200],
    ['o_zab1', 200],
    ['w_vpn1', 201],
    ['w_vpn2', 202],
]
branch_dict = {
    #    ip seg                 gw               nameservers                       bridge
    'w': ['172.25.3.{0}/22',   '172.25.3.254',   ['172.26.1.1', '134.160.4.5'],    'br2.0002'],
    'y': ['10.64.250.{0}/24',  '10.64.250.254',  ['10.64.226.4'],                  'br2.0305'],
    't': ['10.3.5.{0}/25',    '10.3.5.254',     ['10.3.10.1', '134.160.64.241'],  'br2.1115'],
    'k': ['172.21.250.{0}/24', '172.21.250.254', ['172.21.97.5', '134.160.144.2'], 'br2.0890'],
    'o': ['10.5.99.{0}/24',    '10.5.99.254',    ['8.8.8.8'],         'br2.1489'],
}
c7update_image = 'c7update_image'


def create_dhdock(b):
    [
        hostname,
        ip_seed,
    ] = b
    branch_head = hostname[0]
    [
        ip_seg,
        gw,
        nameservers,
        bridge,
    ] = branch_dict[branch_head]
    ip_full = ip_seg.format(str(ip_seed))
    access_ip = ip_full.split('/')[0]
    hex_str_num = ('0' + hex(ip_seed)[2:])[-2:]
    ifaces = [
        {
            'access_ip': True,
            'con_name': 'eth0',
            'autoconnect': True,
            'ip': ip_full,
            'gateway': gw,
            'nameservers': nameservers,
            'search': 'r',
        }
    ]
    vnets = [
        {
            'ifname': 'eth0',
            'mac': f'52:54:00:1f:00:{hex_str_num}',
            'type': 'openvswitch',
            'net_source': bridge
        }
    ]
    add_dict ={
        'vcpu': 2,
        'vmem': 2048,
        'org_hostname': 'localhost',
        'prepare_vdisk': {
            'type': 'copy',
            'org_path': f'/vm_images/{c7update_image}.comp.qcow2',
            'size': 8,
        },
    }
    return r21_c7.create_node_dict(hostname, access_ip, ifaces, vnets, add_dict)


def install(b):
    def func():
        node_dict = create_dhdock(b)
        return r21_c7.base_node.Node(node_dict)

    return func


def create_nodes():
    return [[f'create {b[0]}({b[1]})', install(b)] for b in dhdock_list]


def destroy_nodes():
    return [[f'delete {b[0]}({b[1]})', r21_c7.destroy_node(b[0])] for b in dhdock_list]
