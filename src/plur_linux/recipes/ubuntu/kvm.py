from plur import base_shell


def install(session):
    [base_shell.run(session, a) for a in [
        'sudo apt-get update',
        'sudo apt-get install -y ' + ' '.join([
            'qemu-kvm',
            'libvirt-daemon',
            'libvirt-clients',
            'bridge-utils',
        ])
    ]]

