#! /usr/bin/env python
from mini.ansi_colors import red
from plur import base_shell
from plur import session_wrap


def install_kvm(session):
    base_shell.yum_install(session, {'packages': [
        'qemu-kvm',
        'libvirt',
        'virt-install',
        'virt-manager'
    ]})
    base_shell.service_on(session, 'libvirtd')


@session_wrap.sudo
def configure_nested(session):
    """
    cpu mode in vm must be changed
    <cpu mode='host-model'>
    or
    <cpu mode='host-passthrough'>

    """
    if base_shell.count_by_egrep(session, 'vmx', '/proc/cpuinfo'):
        kvm_vendor = 'kvm_intel'
    elif base_shell.count_by_egrep(session, 'svm', '/proc/cpuinfo'):
        kvm_vendor = 'kvm_amd'
    else:
        print(red('could not find vmx/svm in /proc/cpuinfo'))
        return

    base_shell.here_doc(session, '/etc/modprobe.d/kvm-nested.conf', [
        f'options {kvm_vendor} nested=1'
    ])
    [base_shell.run(session, action) for action in [
        f'modprobe -r {kvm_vendor}',
        f'modprobe {kvm_vendor}',
        f'cat /sys/module/{kvm_vendor}/parameters/nested' # expect output Y
    ]]

