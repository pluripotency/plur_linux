from plur import base_shell
from plur_linux.recipes.centos.docker import setup_docker
from plur_linux.recipes.ops import sshd_config
from plur_linux.recipes.centos import chrony
from plur_linux.nodes import new_node
from plur_linux.nodes.guests import images_ubu

dock_list = [['udock' + ('000' + str(num))[-3:], num] for num in range(101, 105)]

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
    docker_image = images_ubu.ubu_docker_image
    platform = images_ubu.platform

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
    return [['create ' + host[0], install_dock(host)] for host in dock_list]


def destroy_nodes():
    return [['delete ' + host[0], new_node.destroy_node(host[0])] for host in dock_list]
