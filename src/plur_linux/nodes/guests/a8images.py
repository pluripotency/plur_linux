from mini import misc
from nodes import new_node

a8base_image = 'a8base_image'
a8docker_image = 'a8docker_image'
a8desk_image = 'a8desk_image'


def a8base_update(session):
    from recipes.almalinux8 import ops
    ops.a8base_update(session)


def a8_cloudimage(hostname, run_post):
    return new_node.create_single_iface_node_dict(hostname, 'dhcp', {
        'platform': 'almalinux8',
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


def create_a8base_image():
    return a8_cloudimage(a8base_image, [])


def create_a8docker_image():
    from recipes.almalinux8 import docker
    return a8_cloudimage(a8docker_image, [
        a8base_update,
        docker.install,
    ])


def create_a8desk_image():
    def func(session):
        from recipes.almalinux8 import desktop
        desktop.install_gui(session)
        desktop.install_xrdp(session)

    return a8_cloudimage(a8desk_image, [
        a8base_update,
        func
    ])


def create_destroy_node(hostname):
    return new_node.destroy_node_dict(hostname)


def create_nodes():
    return [
        ['create ' + a8base_image, create_a8base_image],
        ['create ' + a8docker_image, create_a8docker_image],
        ['create ' + a8desk_image, create_a8desk_image],
    ]


def destroy_nodes():
    return [['delete ' + hostname, create_destroy_node(hostname)] for hostname in [
        a8base_image
        , a8docker_image
        , a8desk_image
    ]]
