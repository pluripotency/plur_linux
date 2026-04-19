from plur import base_shell
from plur_linux.recipes.ubuntu import ops
from mini import misc

def install(session):
    ops.sudo_apt_get_install_y([
        'sudo apt -y install qemu-kvm libvirt-daemon-system libvirt-daemon virtinst bridge-utils libosinfo-bin virt-manager openvswitch-switch'
    ])(session)
    _ = [base_shell.run(session, action) for action in misc.del_indent_lines("""
    sudo usermod -aG libvirt $(whoami)
    sudo systemctl restart libvirtd
    newgrp libvirt
    """)]

netplan_str = """
# replace /etc/netplan/50-cloud-init.yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    eno1:
      # dhcp4: true
      dhcp4: no
      dhcp6: no
  openvswitch: {}
  bridges:
    br0:
      interfaces: [eno1]
      openvswitch: {}
      addresses:
        - 192.168.0.70/24
      nameservers:
        addresses:
          - 8.8.8.8
          - 8.8.4.4
      routes:
        - to: default
          via: 192.168.0.1
"""

