from plur_linux.recipes.openvswitch import redhat


def install(session):
    return redhat.install_openvswitch_for_almalinux9(session)
