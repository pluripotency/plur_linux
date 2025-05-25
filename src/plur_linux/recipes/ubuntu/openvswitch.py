from plur import base_shell


def install_openvswitch(session):
    base_shell.run(session, 'sudo apt install -y openvswitch-switch')
