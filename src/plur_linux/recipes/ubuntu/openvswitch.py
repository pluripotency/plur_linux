from plur_linux.recipes.ubuntu import ops


def install_openvswitch(session):
    ops.sudo_apt_get_install_y(['openvswitch-switch'])(session)
