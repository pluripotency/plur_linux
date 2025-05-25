from nodes import new_node
a9base_image =   'a9baseimage'
a9docker_image = 'a9dockerimage'
a9desk_image =   'a9deskimage'

def a9base_update(session):
    from recipes.almalinux9 import ops
    ops.a9base_update(session)

def a9_cloudimage(hostname, run_post):
    return new_node.create_single_iface_node_dict(hostname, 'dhcp', {
        'platform': 'almalinux9',
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

def create_a9base_image():
    return a9_cloudimage(a9base_image, [])

def create_a9docker_image():
    from recipes.almalinux9 import docker
    return a9_cloudimage(a9docker_image, [
        a9base_update,
        docker.install,
    ])

def create_a9desk_image():
    def func(session):
        from recipes.almalinux9 import desktop
        desktop.install_gui(session)
        desktop.install_xrdp(session)

    return a9_cloudimage(a9desk_image, [
        a9base_update,
        func
    ])

def create_nodes():
    return [
        ['create ' + a9base_image,   create_a9base_image],
        ['create ' + a9docker_image, create_a9docker_image],
        ['create ' + a9desk_image,   create_a9desk_image],
    ]

def destroy_nodes():
    return [['delete ' + hostname, new_node.destroy_node(hostname)] for hostname in [
        a9base_image
        , a9docker_image
        , a9desk_image
    ]]
