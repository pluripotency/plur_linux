from mini import menu
from nodes import util
from recipes.ops import ops
from nodes import new_c7
from nodes.guests.images import gluster_image
from recipes.centos.glusterfs import vol, gluster
gl41_image_comp = f'{gluster_image}.comp.qcow2'

create_base_node = new_c7.create_base_node

HEAD_KGL = 'kgl'
hosts_kgl = [[HEAD_KGL + ('000' + str(num))[-3:], num] for num in range(24, 27)]

def select_num_and_hostlist():
    host_list = hosts_kgl
    selected_num = menu.choose_num([host[0] for host in host_list])
    return selected_num, host_list


def create_gluster_dict(hv='kvm'):
    selected_num, host_list = select_num_and_hostlist()
    ip_seed = host_list[selected_num][1]
    hostname = host_list[selected_num][0]

    if hv == 'kvm':
        # gl41_image is needed
        size_str = menu.get_input(r'\d{1,3}G', 'size of vdb by G:', 'err: input size ex) 100G', '100G')
        options = {
            'prepare_vdisk': {
                'org_path': f'/vm_images/{gl41_image_comp}',
                'type': 'copy',
                'size': None
            },
            'additional_vdisks': [{
                'format': 'raw',
                'size': size_str,
                'dev_name': 'vdb'
            }]
        }
    else:
        options = {}

    node_dict = create_base_node(hostname, ip_seed, options)
    segment = node_dict['ifaces'][0]['segment']
    hosts = [[segment['ip_base_prefix'] + f'.{host[1]}', host[0]] for host in host_list]
    if hv == 'kvm':
        run_post = [
            ops.create_hosts(hosts),
            vol.add_disk(),
            gluster.install_server
        ]
    else:
        run_post = [
            ops.create_hosts(hosts),
            vol.add_disk(dev='/dev/sdb'),
            gluster.install_server
        ]
    node_dict['setups'] = {'run_post': run_post}
    return node_dict


def create_gluster_on_kvm():
    return create_gluster_dict()


def create_gluster_on_vmware():
    # need to prepare sdb and gluster-server setup
    return create_gluster_dict(hv='vmware')


def create_replica():
    selected_num, host_list = select_num_and_hostlist()
    ip_seed = host_list[selected_num][1]
    hostname = host_list[selected_num][0]
    node_dict = create_base_node(hostname, ip_seed)
    node_dict['setups'] = {'run_post': [
        vol.create_replica_on_first([host[0] for host in host_list]),
    ]}
    return node_dict


def create_nodes():
    return [
        ['create gluster on kvm', create_gluster_on_kvm],
        ['create gluster on vmware', create_gluster_on_vmware],
        ['create replica 2:', create_replica],
    ]


def destroy_node():
    selected_num, host_list = select_num_and_hostlist()
    hostname = host_list[selected_num][0]
    return util.node(new_c7.destroy_c7_dict(hostname))


def destroy_nodes():
    return [
        ['delete gluster node', destroy_node],
    ]
