from recipes.openvswitch import redhat


def install(session):
    redhat.dict_ovs['almalinux9']['caracal'](session)
