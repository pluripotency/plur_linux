from plur import base_shell
from plur import session_wrap


def esxi_str(pxe=True):
    name = 'esxi67'
    cpu = 4
    ram = 8 * 1024
    ovs_br = 'br2.4084'
    disk_size = 80
    disk_path = f'/var/lib/libvirt/images/{name}.img,size={disk_size},bus=sata'
    network = f'bridge={ovs_br},model=e1000,virtualport_type=openvswitch'
    option_lines = [
        'virt-install'
        , f'--name {name}'
        , f'--ram {ram}'
        , f'--disk path={disk_path}'
        , '--cpu host-passthrough'
        , f'--vcpus={cpu}'
        , '--os-type linux'
        , '--os-variant=virtio26'
        , f'--network {network}'
        , '--graphics spice,listen=0.0.0.0'
        , '--video qxl'
        , '--features kvm_hidden=on'
        , '--machine q35'
    ]
    if pxe:
        option_lines += [
            '--pxe',
        ]
    else:
        iso_name = 'VMware-VMvisor-Installer-6.5.0-4564106.x86_64.iso'
        iso_path = f'/var/lib/libvirt/images/{iso_name}'
        option_lines += [
            f'--cdrom {iso_path}'
        ]
    return ' \\'.join(option_lines)


@session_wrap.sudo
def pxe_install_esxi(session):
    # esxpxe67 is needed for pxe install
    # before this, nested kvm must be enabled
    base_shell.run(session, esxi_str())

