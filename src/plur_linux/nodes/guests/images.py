from mini import misc
from plur import base_shell
from plur_linux.recipes.centos import chrony
from plur_linux.recipes import firewalld
from plur_linux.nodes import new_node

a8base_image = 'a8base_image'
a8docker_image = 'a8docker_image'
a8desk_image = 'a8desk_image'

c7base_image = 'c7base_image'
c7desk_image = 'c7desk_image'

rsyslog_image = 'rsyslog_image'
gluster_image = 'gl41_image'
dhguest_image = 'dhguest_c7_img'
dhguest_desk_image = 'dhguest_c7_desk_img'


def a8base_update(session):
    from plur_linux.recipes.almalinux8 import ops
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
    return misc.Node(a8_cloudimage(a8base_image, []))


def create_a8docker_image():
    from plur_linux.recipes.almalinux8 import docker
    return misc.Node(a8_cloudimage(a8docker_image, [
        a8base_update,
        docker.install,
    ]))


def create_a8desk_image():
    def func(session):
        from plur_linux.recipes.almalinux8 import desktop
        desktop.install_gui(session)
        desktop.install_xrdp(session)

    return misc.Node(a8_cloudimage(a8desk_image, [
        a8base_update,
        func
    ]))


def c7base_update(session):
    from plur_linux.recipes.ops import ops
    ops.c7base_update(session)
    base_shell.run(session, 'sudo yum install -y ' + ' '.join([
        'wget'
        , 'dos2unix'
        , 'httping'
        , 'bind-utils'
        , 'fping'
    ]))


def c7_cloudimage(hostname, run_post):
    return new_node.create_single_iface_node_dict(hostname, 'dhcp', {
        'prepare_vdisk': {
            'type': 'cloud_image',
            'size': 8,
        },
        'imagefy': {
            'hostname': 'localhost',
            'compress_to': f'/vm_images/{hostname}.comp.qcow2'
        },
        'setups': {
            'run_post': run_post
        }
    })


def create_c7base_image():
    return misc.Node(c7_cloudimage(c7base_image, c7base_update))


def create_c7desk_image():
    def desk_setup(session):
        firewalld.configure(services=['ssh'], ports=['3389/tcp'], add=True)(session)
        from plur_linux.recipes.centos.desktop import c7
        c7.minimul_to_mindesk(session)
        from plur_linux.recipes.centos import xrdp
        xrdp.install(session)
        c7.configure_desktop(session)
        base_shell.run(session, 'sudo rm -f /etc/sysconfig/network-scripts/ifcfg-eth0')

    return misc.Node(c7_cloudimage(c7desk_image, [
        c7base_update,
        desk_setup,
    ]))


def create_rsyslog_image():
    def get_rsyslog_packages(session):
        base_shell.yum_install(session, {
            'update': True,
            'packages': [
                'vim'
                , 'rsyslog-udpspoof'
                , 'firewalld'
            ]})
        chrony.configure(session)
        base_shell.run(session, 'sudo yum clean all')

    return misc.Node(c7_cloudimage(rsyslog_image, get_rsyslog_packages))


def create_gluster_image():
    from plur_linux.recipes.centos.glusterfs import gluster
    return misc.Node(c7_cloudimage(gluster_image, gluster.install_server))


def dhguest_update(session):
    from plur_linux.recipes.centos import chrony
    chrony.configure(session)
    from plur_linux.recipes.ops import ops
    ops.disable_selinux(session)
    ops.disable_ipv6(session)
    firewalld.configure(services=['ssh'], add=True)(session)

    base_shell.yum_install(session, {
        'update': True,
        'packages': ['epel-release'],
    })
    base_shell.yum_install(session, {'packages': [
        'wget'
        , 'dos2unix'
        , 'httping'
        , 'bind-utils'
        , 'fping'
    ]})


def create_dhguest_image():
    def dhguest_setup(session):
        dhguest_update(session)
        base_shell.run(session, 'sudo rm -f /etc/sysconfig/network-scripts/ifcfg-eth0')

    node_dict = new_node.create_single_iface_node_dict(dhguest_image, 'dhcp', {
        'ifaces': [{
            # 'nm_controlled': True,
            'access_ip': True,
            'con_name': 'eth0',
            'autoconnect': True,
            # 'autoconnect': False,
            'ip_seed': 'dhcp'
        }],
        'prepare_vdisk': {
            'type': 'copy',
            'org_path': f'/vm_images/{c7base_image}.comp.qcow2',
            'size': 8,
        },
        'imagefy': {
            'compress_to': f'/vm_images/{dhguest_image}.comp.qcow2',
        },
        'setups': {
            'run_post': dhguest_setup
        }
    })
    return misc.Node(node_dict)


def create_dhguest_desk_image():
    def dhguest_desk_setup(session):
        dhguest_update(session)

        firewalld.configure(services=['ssh'], ports=['3389/tcp'], add=True)(session)
        from plur_linux.recipes.centos.desktop import c7
        c7.minimul_to_mindesk(session)
        from plur_linux.recipes.centos import xrdp
        xrdp.install(session)
        c7.configure_desktop(session)
        base_shell.run(session, 'sudo yum install -y seahorse')

        base_shell.service_off(session, 'NetworkManager')
        # base_shell.run(session, 'sudo yum remove -y NetworkManager')

        base_shell.run(session, 'sudo rm -f /etc/sysconfig/network-scripts/ifcfg-eth0')

    node_dict = new_node.create_single_iface_node_dict(dhguest_desk_image, 'dhcp', {
        'ifaces': [{
            # 'nm_controlled': True,
            'access_ip': True,
            'con_name': 'eth0',
            'autoconnect': True,
            # 'autoconnect': False,
            'ip_seed': 'dhcp'
        }],
        'prepare_vdisk': {
            'type': 'copy',
            'org_path': f'/vm_images/{c7desk_image}.comp.qcow2',
            'size': 8,
        },
        'imagefy': {
            'compress_to': f'/vm_images/{dhguest_desk_image}.comp.qcow2',
            # 'keep': True,
        },
        'setups': {
            'run_post': dhguest_desk_setup
        }
    })
    return misc.Node(node_dict)


def create_k3os():
    hostname = 'k3os1'
    node_dict = new_node.create_single_iface_node_dict(hostname, 'dhcp', {
        'prepare_vdisk': {
            'type': 'blank',
            'size': 8
        },
        'cdrom': '/home/worker/Downloads/k3os-amd64.iso'
    })
    return misc.Node(node_dict)


def create_destroy_node(hostname):
    return misc.Node(new_node.destroy_node_dict(hostname))


def create_nodes():
    return [
        ['create ' + a8base_image, create_a8base_image],
        ['create ' + a8docker_image, create_a8docker_image],
        ['create ' + a8desk_image, create_a8desk_image],
        ['create ' + c7base_image, create_c7base_image],
        ['create ' + c7desk_image, create_c7desk_image],
        ['create ' + rsyslog_image, create_rsyslog_image],
        ['create ' + dhguest_image, create_dhguest_image],
        ['create ' + dhguest_desk_image, create_dhguest_desk_image],
        ['create ' + gluster_image, create_gluster_image],
        ['create k3os1', create_k3os],
    ]


def destroy_nodes():
    return [['delete ' + hostname, create_destroy_node(hostname)] for hostname in [
        a8base_image
        , a8docker_image
        , a8desk_image
        , c7base_image
        , c7desk_image
        , rsyslog_image
        , dhguest_image
        , dhguest_desk_image
        , gluster_image
        , 'k3os'
    ]]
