from plur import base_shell
from plur_linux.recipes.ubuntu import ops as ubuntu_ops
from plur_linux.nodes import new_node
from plur_linux.recipes.ubuntu import docker_ce

platform = 'noble'
ubu_image = 'ubu_image'
ubu_docker_image = 'ubu_docker_image'
ubu_docker_desk_image = 'ubu_docker_desk_image'

def base_update(session):
    ubuntu_ops.configure_systemd_timesyncd(session)
    ubuntu_ops.sudo_apt_upgrade(session)
    base_shell.run(session, 'apt-get clean')

def ubu_cloudimage(hostname, run_post):
    return new_node.create_single_iface_node_dict(hostname, 'dhcp', {
        'platform': platform,
        'prepare_vdisk': {
            'type': 'cloud_image',
            'size': 10,
        },
        'imagefy': {
            'hostname': 'localhost',
            'compress_to': f'/vm_images/{hostname}.comp.qcow2'
        },
        'setups': {
            'run_post': run_post
        }
    })

def create_ubu_image():
    return ubu_cloudimage(ubu_image, [
        base_update,
    ])

def create_docker_image():
    return ubu_cloudimage(ubu_docker_image, [
        base_update,
        docker_ce.install,
    ])

def create_nodes():
    return [
        ['create ' + ubu_image, create_ubu_image()],
        ['create ' + ubu_docker_image, create_docker_image()],
    ]

def destroy_nodes():
    return [['delete ' + hostname, new_node.destroy_node(hostname)] for hostname in [
        ubu_image,
        ubu_docker_image,
    ]]
