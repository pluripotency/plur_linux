from mini import misc


def virt_install_str(name, option_list, os_variant='almalinux8', cpu=2, mem=2048):
    opt_str = ''.join([f'  {opt} \\\n    ' for opt in option_list])
    return misc.del_indent(rf"""
    sudo virt-install \
      --name {name} --vcpus={cpu} --ram {mem} \
    {opt_str}  --os-variant={os_variant} \
      --accelerate \
      --graphics vnc,listen=127.0.0.1 \
      --noreboot \
      --noautoconsole

    """)


def create_vnet_opt_str(vnet):
    """
    vnet: {
        'mac':
        'type':
        'net_source':
    }
    """
    mac = vnet['mac']
    net_type = 'default'
    if 'type' in vnet:
        net_type = vnet['type']
    net_source = vnet['net_source']
    if net_type == 'openvswitch':
        vnet_opt_str = f'--network bridge={net_source},model=virtio,mac={mac},virtualport_type=openvswitch'
    elif net_type == 'bridge':
        vnet_opt_str = f'--network bridge={net_source},model=virtio,mac={mac}'
    elif net_type == 'direct':
        vnet_opt_str = f'--network type=direct,source={net_source},model=virtio,mac={mac}'
    elif net_type == 'default':
        vnet_opt_str = f'--network network={net_source},model=virtio,mac={mac}'
    else:
        vnet_opt_str = f'--network network={net_source},model=virtio,mac={mac}'
    return vnet_opt_str


def virt_install_sh_cloudinit_str(name, bridge, disk_full_path, iso_full_path, os_variant='almalinux8', cpu=2, mem=2048):
    """
    >>> print(virt_install_sh_cloudinit_str('a8cinit', 'br0', '/vm_images/a8cinit.qcow2' ,'/tmp/seed.iso'))
    #! /bin/bash
    NAME=a8cinit
    BRIDGE=br0
    DISK_PATH=/vm_images/a8cinit.qcow2
    ISO_PATH=/tmp/seed.iso
    <BLANKLINE>
    sudo virt-install \\
      --name $NAME --vcpus=2 --ram 2048 \\
      --boot hd \\
      --disk $DISK_PATH,cache=none --cdrom=$ISO_PATH \\
      --network bridge=$BRIDGE,virtualport_type=openvswitch \\
      --os-variant=almalinux8 \\
      --accelerate \\
      --graphics vnc,listen=127.0.0.1 \\
      --noreboot \\
      --noautoconsole
    <BLANKLINE>
    """
    option_list = ['--boot hd']
    option_list += [f"--disk $DISK_PATH,cache=none --cdrom=$ISO_PATH"]
    option_list += ['--network bridge=$BRIDGE,virtualport_type=openvswitch']
    return misc.del_indent(f"""
    #! /bin/bash
    NAME={name}
    BRIDGE={bridge}
    DISK_PATH={disk_full_path}
    ISO_PATH={iso_full_path}
    
    
    """) + virt_install_str('$NAME', option_list, os_variant, cpu, mem)


def virt_install_os_iso_with_ks_str(name, bridge, disk_full_path, disk_size_g, os_iso_path, os_variant='almalinux8', cpu=2, mem=2048):
    """

    """
    option_list = ["--boot hd --initrd-inject=./a8.ks --extra-args 'inst.ks=file:/a8.ks'"]
    option_list += [f"--network bridge={bridge},virtualport_type=openvswitch"]
    option_list += [f"--disk {disk_full_path},size={disk_size_g},sparse=yes,cache=none --location={os_iso_path}"]
    return virt_install_str(name, option_list, os_variant, cpu, mem)


def esx_virt_install_a8_pxe_str():
    source_sh = misc.del_indent(r"""
    #! /bin/sh

    VM_NAME=a8esxi
    V_MEM=16384
    V_CPU=4
    DISK_PATH=/vm_images/a8esxi.img
    BRIDGE=br2.4084
    NETWORK=bridge=${BRIDGE},model=e1000e,virtualport_type=openvswitch

    virt-install \
        --name ${VMNAME} \
        --ram ${V_MEM} \
        --disk path=${DISK_PATH},size=80,bus=sata \
        --cpu host-passthrough \
        --vcpus=${V_CPU} \
        --os-variant=fedora-unknown \
        --network ${NETWORK} \
        --graphics spice,listen=0.0.0.0 \
        --video qxl \
        --pxe \
        --features kvm_hidden=on \
        --machine q35
    """)
    return source_sh


def esx_virt_install_a8_str():
    source_sh = misc.del_indent(r"""
    #! /bin/sh

    VM_NAME=esxi70
    V_MEM=16384
    V_CPU=4
    DISK_PATH=/vm_images/esxi70.img
    ISO_PATH=/vm_images/VMware-VMvisor-Installer-7.0b-16324942.x86_64.iso
    BRIDGE=br2.4084
    NETWORK=bridge=${BRIDGE},model=e1000e,virtualport_type=openvswitch

    virt-install \
        --name ${VMNAME} \
        --ram ${V_MEM} \
        --disk path=${DISK_PATH},size=80,bus=sata \
        --cpu host-passthrough \
        --vcpus=${V_CPU} \
        --os-variant=fedora-unknown \
        --network ${NETWORK} \
        --graphics spice,listen=0.0.0.0 \
        --video qxl \
        --cdrom ${ISO_PATH} \
        --features kvm_hidden=on \
        --machine q35
    """)
    return source_sh


