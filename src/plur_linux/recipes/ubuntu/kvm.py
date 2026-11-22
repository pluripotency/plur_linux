from plur import base_shell
from plur_linux.recipes.ubuntu import ops
from mini import misc

def install_resolute(session):
    ops.sudo_apt_get_install_y([
        'qemu-system qemu-utils libvirt-clients virt-manager libvirt-daemon-system libvirt-daemon virtinst libosinfo-bin openvswitch-switch'
    ])(session)
    _ = [base_shell.run(session, action) for action in misc.del_indent_lines("""
    sudo usermod -aG libvirt $(whoami)
    sudo systemctl restart libvirtd
    newgrp libvirt
    """)]

def install(session):
    ops.sudo_apt_get_install_y([
        'qemu-kvm libvirt-daemon-system libvirt-daemon virtinst bridge-utils libosinfo-bin virt-manager openvswitch-switch'
    ])(session)
    _ = [base_shell.run(session, action) for action in misc.del_indent_lines("""
    sudo usermod -aG libvirt $(whoami)
    sudo systemctl restart libvirtd
    newgrp libvirt
    """)]

