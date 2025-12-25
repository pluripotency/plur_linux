from plur_linux.nodes import new_node
from plur_linux.recipes.kubernetes import common
from plur_linux.recipes.kubernetes import kubeadm

platform = 'almalinux9'
host_list = [
    ['mgr081', 81],
    ['ctl082', 82],
    ['wkr083', 83],
    ['wkr084', 84],
]


def choose_host(host):
    def func():
        [
            hostname,
            ip_seed
        ] = host
        login_user = 'worker'
        vnets = [{
            'ifname': 'eth0',
            'mac': new_node.random_mac()
        }]
        ifaces = [{
            'access_ip': True,
            'con_name': 'eth0',
            'autoconnect': True,
            'ip_seed': ip_seed
        }]
        bound_env = new_node.env_ops.EnvSegments().bind_env({
            'ifaces': ifaces,
            'vnets': vnets
        })
        iface = bound_env['ifaces'][0]
        access_ip = iface['ip'].split('/')[0]
        segment = iface['segment']
        host_lines = [f'{segment["ip_base_prefix"]}.{host[1]} {host[0]}' for host in host_list]
        mgr_ip = f'{segment["ip_base_prefix"]}.{host_list[0][1]}'
        ctl_ip = f'{segment["ip_base_prefix"]}.{host_list[1][1]}'

        user_list = new_node.env_ops.get_current_index_user_list()
        login_password = ''
        for user in user_list:
            if user['username'] == login_user:
                login_password = user['password']
        for iface in bound_env['ifaces']:
            if 'access_ip' in iface and iface['access_ip']:
                access_ip = iface['ip'].split('/')[0]
        login_waitprompt = new_node.base_node.get_linux_waitprompt(platform, hostname, login_user)

        run_post = lambda : None
        if hostname.startswith('mgr'):
            run_post = common.setup_manager_node(host_lines, ctl_ip)
        elif hostname.startswith('ctl'):
            run_post = kubeadm.setup_control_plane(host_lines, mgr_ip, ctl_ip)
        elif hostname.startswith('wkr'):
            run_post = kubeadm.setup_worker_node(host_lines)
        node_dict = new_node.concat_dict([
            {
                'ssh_options': '-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null',
                'ifaces': bound_env['ifaces'],
                'vnets': bound_env['vnets']
            },
            {
                'access_ip': access_ip,
                'platform': platform,
                'vcpu': 2,
                'vmem': 4096,
                'prepare_vdisk': {
                    'type': 'cloud_image',
                    'size': 30,
                },
                'setups': {
                    'run_post': run_post
                }
            },
            {

                'hostname': hostname,
                'username': login_user,
                'password': login_password,
                'waitprompt': login_waitprompt,
            }
        ])
        return node_dict
    return func


def create_nodes():
    return [['setup ' + host[0], choose_host(host)] for host in host_list]


def destroy_nodes():
    return [['delete kubeadm node: ' + host[0], new_node.destroy_node(host[0])] for host in host_list]

