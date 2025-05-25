from plur import base_shell
from mini import misc
from recipes import firewalld
from recipes.centos.docker import setup_docker
from recipes.ops import sshd_config
from recipes.centos.glusterfs import gluster
from recipes.centos import chrony
from nodes import new_node

dock_list = [['dock' + ('000' + str(num))[-3:], num] for num in range(101, 105)]
a8dock_list = [['a8dock' + ('000' + str(num))[-3:], num] for num in range(105, 109)]
dock_gl41r_list = [['dock' + ('000' + str(num))[-3:], num] for num in range(101, 107)]
labdock_host_list = [['lab' + ('000' + str(num))[-3:], num] for num in range(64, 66)]
min_dock_list = [[f"dock{('000' + str(num))[-3:]}", num] for num in range(101, 103)]

branch_dict = {
    #    ip seg                 gw                bridge     syslog_segment
    'w': ['172.25.2.{0}/22',   '172.25.3.254',   'br2.0002', '172.25.3'],
    'y': ['10.64.244.{0}/23',  '10.64.245.254',  'br2.0313', '10.64.250'],
    't': ['10.3.96.{0}/23',    '10.3.97.254',    'br2.1117', '10.3.5'],
    'k': ['172.21.244.{0}/23', '172.21.245.254', 'br2.0883', '172.21.250'],
    'o': ['10.5.76.{0}/23',    '10.5.77.254',    'br2.1476', '10.5.99'],
}

def install_base(session):
    chrony.configure(session)
    if not base_shell.check_command_exists(session, 'git'):
        base_shell.yum_install(session, {
            'update': False,
            # 'update': True,
            'packages': [
                'tmux',
                'git',
                'vim',
            ]
        })
    setup_docker.install_docker_if_not_installed(session)


def install_dock(dock):
    [
        hostname
        , ip_seed
    ] = dock
    if hostname.startswith('a8dock'):
        platform = 'almalinux8'
        docker_image = 'a8docker_image'
    else:
        platform = 'almalinux9'
        docker_image = 'a9dockerimage'

    def run_post(session):
        sshd_config.apply_policy(sshd_config.strict_server(pass_auth='yes'))(session)

    return lambda: new_node.create_single_iface_node_dict(hostname, ip_seed, {
        'vcpu': 2,
        'vmem': 2048,
        'platform': platform,
        'prepare_vdisk': {
            'type': 'copy',
            'cloudinit': True,
            'org_path': f'/vm_images/{docker_image}.comp.qcow2',
            'size': 16,
        },
        'setups': {
            'run_post': run_post
        }
    }, 'worker')

def create_nodes():
    return [['create ' + host[0], install_dock(host)] for host in dock_list] + \
        [['create ' + host[0], install_dock(host)] for host in a8dock_list]


def destroy_nodes():
    return [['delete ' + host[0], new_node.destroy_node(host[0])] for host in dock_list] + \
        [['delete ' + host[0], new_node.destroy_node(host[0])] for host in a8dock_list]
