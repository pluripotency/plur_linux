from plur import base_shell
from nodes.util import *
from recipes.ubuntu import ops as ubuntu_ops
from nodes import new_node
from recipes.ubuntu import docker_ce

ubu_update_image = 'ubu_update_image'
ubu_docker_image = 'ubu_docker_image'
ubu_docker_desk_image = 'ubu_docker_desk_image'
ubu_gluster_image = 'ubu_gl41_image'
ubu_dhguest_image = 'dhguest_ubu_img'
ubu_dhguest_desk_image = 'dhguest_ubu_desk_img'


def base_update(session):
    ubuntu_ops.configure_systemd_timesyncd(session)
    ubuntu_ops.sudo_apt_upgrade(session)
    base_shell.run(session, 'apt-get clean')


def create_ubu_base_image():
    def func():
        ubu_update_image
        node_dict = new_node.create_single_iface_node_dict(ubu_update_image, 'dhcp', {
            'platform': 'ubuntu',
            'prepare_vdisk': {
                'type': 'cloud_image',
                'size': 8,
            },
            'imagefy': {
                'hostname': 'localhost',
                'compress_to': f'/vm_images/{ubu_update_image}.comp.qcow2'
            },
            'setups': {
                'run_post': base_update
            }
        })
        return node(node_dict)
    return func


def create_docker_image():
    def func():
        node_dict = new_node.create_single_iface_node_dict(ubu_docker_image, 'dhcp', {
            'platform': 'ubuntu',
            'prepare_vdisk': {
                'type': 'cloud_image',
                'size': 8,
            },
            'imagefy': {
                'compress_to': f'/vm_images/{ubu_docker_image}.comp.qcow2'
            },
            'setups': {
                'run_post': [
                    docker_ce.install
                ]
            }
        })
        return node(node_dict)
    return func


def create_destroy_node(hostname):
    return node(new_node.destroy_node_dict(hostname))


def create_nodes():
    return [
        ['create ' + ubu_update_image, create_ubu_base_image()],
        ['create ' + ubu_docker_image, create_docker_image()],
    ]


def destroy_nodes():
    return [['delete' + hostname, create_destroy_node(hostname)] for hostname in [

        ubu_update_image
        , ubu_docker_image
    ]]
