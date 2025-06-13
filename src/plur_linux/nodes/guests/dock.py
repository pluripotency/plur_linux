from plur import base_shell
from mini import misc
from plur_linux.recipes import firewalld
from plur_linux.recipes.centos.docker import setup_docker
from plur_linux.recipes.ops import sshd_config
from plur_linux.recipes.centos.glusterfs import gluster
from plur_linux.recipes.centos import chrony
from plur_linux.nodes import new_node

dock_list = [['dock' + ('000' + str(num))[-3:], num] for num in range(101, 105)]
a8dock_list = [['a8dock' + ('000' + str(num))[-3:], num] for num in range(105, 109)]
dock_gl41r_list = [['dock' + ('000' + str(num))[-3:], num] for num in range(101, 107)]
labdock_host_list = [['lab' + ('000' + str(num))[-3:], num] for num in range(64, 66)]
min_dock_list = [[f"dock{('000' + str(num))[-3:]}", num] for num in range(101, 103)]

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
