import re
from mini import misc
from mini import ansi_colors
from plur import session_wrap
from plur import base_shell
from plur_linux.recipes import firewalld
from plur_linux.recipes.pxe import docker_nginx
from plur_linux.recipes.pxe import docker_dhcpd
from plur_linux.recipes.pxe import docker_tftpd
from plur_linux.recipes.pxe import kickstart
from plur_linux.recipes.pxe import prepare_iso
tftpboot_dir=docker_tftpd.tftpboot_dir

def pxe_menu_pre_str(menu='menu'):
    """
    >>> print(pxe_menu_pre_str('vesamenu.c32'))
    default vesamenu.c32
    prompt 0
    # timeout 300 means 30sec
    timeout 300
    totaltimeout 6000
    ontimeout local
    <BLANKLINE>
    display boot.msg
    <BLANKLINE>
    """
    return misc.del_indent(f"""
    default {menu}
    prompt 0
    # timeout 300 means 30sec
    timeout 300
    totaltimeout 6000
    ontimeout local

    display boot.msg

    """)

def pxe_menu_entry_str(dist_name, pxe_ip, dist_dir, ks):
    """
    >>> print(pxe_menu_entry_str('AlmaLinux 8', '192.168.10.154', 'almalinux8', 'a8_vda.ks'))
    label linux
      menu label ^Install AlmaLinux 8 with a8_vda.ks
      kernel almalinux8/vmlinuz
      append initrd=almalinux8/initrd.img ip=dhcp inst.text inst.ks=http://192.168.10.154/ks/a8_vda.ks
    <BLANKLINE>
    """
    inst_ks = f'inst.ks=http://{pxe_ip}/ks/{ks}'
    return misc.del_indent(f"""
    label linux
      menu label ^Install {dist_name} with {ks}
      kernel {dist_dir}/vmlinuz
      append initrd={dist_dir}/initrd.img ip=dhcp inst.text {inst_ks}

    """)

def pxe_menu_entry_no_ks_str(dist_name, pxe_ip, dist_dir):
    """
    >>> print(pxe_menu_entry_no_ks_str('AlmaLinux 8', '192.168.10.154', 'almalinux8'))
    label linux_no_ks
      menu label ^Install AlmaLinux 8 interact
      kernel almalinux8/vmlinuz
      append initrd=almalinux8/initrd.img ip=dhcp inst.repo=http://192.168.10.154/almalinux8
    label rescue
      menu label ^Rescue AlmaLinux 8
      kernel almalinux8/vmlinuz
      append initrd=almalinux8/initrd.img rescue
    <BLANKLINE>
    """
    inst_repo = f'inst.repo=http://{pxe_ip}/{dist_dir}'
    return misc.del_indent(f"""
    label linux_no_ks
      menu label ^Install {dist_name} interact
      kernel {dist_dir}/vmlinuz
      append initrd={dist_dir}/initrd.img ip=dhcp {inst_repo}
    label rescue
      menu label ^Rescue {dist_name}
      kernel {dist_dir}/vmlinuz
      append initrd={dist_dir}/initrd.img rescue
    
    """)

def create_pxe_menu_str(dist_name, pxe_ip, dist_dir, ks_filename_list):
    value = pxe_menu_pre_str()
    for ks in ks_filename_list:
        value += pxe_menu_entry_str(dist_name, pxe_ip, dist_dir, ks)
    value += pxe_menu_entry_no_ks_str(dist_name, pxe_ip, dist_dir)
    value += misc.del_indent("""
    label local
      menu label Boot from ^local drive
      localboot 0xffff

    """)
    return value

def prepare_pxe_files(session):
    [base_shell.run(session, a) for a in [
        'dnf -y install syslinux'
        , rf'\cp -f /usr/share/syslinux/pxelinux.0 {tftpboot_dir}/'
        , r'\cp -f /usr/share/syslinux/{menu.c32,vesamenu.c32,ldlinux.c32,libcom32.c32,libutil.c32} ' + f'{tftpboot_dir}/'
    ]]

def prepare_pxe_vmlinuz(session, dist_dir, www_iso_dir):
    base_shell.run(session, f'mkdir -p {tftpboot_dir}/{dist_dir}')
    base_shell.run(session, rf'\cp -f {www_iso_dir}/images/pxeboot/' + '{vmlinuz,initrd.img}' + f' {tftpboot_dir}/{dist_dir}/')

def prepare_pxe_uefi_files(session, grub_cfg_str):
    base_shell.work_on(session, '/root/rpm')
    # base_shell.run(session, 'dnf -y install --downloadonly --downloaddir=/root/rpm shim grub2-efi-x64')
    base_shell.run(session, 'dnf download shim grub2-efi-x64')
    [base_shell.run(session, a) for a in misc.del_indent_lines(rf"""
    rpm2cpio shim-x64-*.rpm | cpio -dimv
    rpm2cpio grub2-efi-x64-*.rpm | cpio -dimv
    \cp -f ./boot/efi/EFI/BOOT/BOOTX64.EFI {tftpboot_dir}/
    \cp -f ./boot/efi/EFI/almalinux/grubx64.efi {tftpboot_dir}/
    """)]
    base_shell.run(session, f"chmod 644 {tftpboot_dir}/" + r"{BOOTX64.EFI,grubx64.efi}")
    base_shell.here_doc(session, f'{tftpboot_dir}/grub.cfg', grub_cfg_str.split('\n'))

def create_grub_cfg_str(dist_name, pxe_ip, dist_dir, ks_filename_list):
    inst_repo = f'inst.repo=http://{pxe_ip}/{dist_dir}'
    value = 'set timeout=30\n'
    for ks in ks_filename_list:
        inst_ks = f'inst.ks=http://{pxe_ip}/ks/{ks}'
        value += '\n'.join([
            f"menuentry 'Install {dist_name} with {ks}' " + "{"
            , f'    linuxefi {dist_dir}/vmlinuz ip=dhcp {inst_ks}'
            , f'    initrdefi {dist_dir}/initrd.img'
            , '}\n'
        ])
    value += '\n'.join([
        f"menuentry 'Install {dist_name}' " + '{'
        , f'    linuxefi {dist_dir}/vmlinuz ip=dhcp {inst_repo}'
        , f'    initrdefi {dist_dir}/initrd.img'
        , '}\n'
    ])
    return value

def get_primary_ip(session):
    primary_ip = None
    for line in base_shell.run(session, 'ip -4 -br a | cat').splitlines():
        if not primary_ip and re.search('^eth', line):
            primary_ip = re.split(r'\s+', line)[2].split('/')[0]
    if not primary_ip:
        print(ansi_colors.red("Couldn't get pxe_ip"))
        exit(1)
    return primary_ip

def to_dist_dir(dist_name: str):
    return dist_name.replace(' ', '').lower()

def by_sudo_pxe(dist_name, pxe_ip, www_iso_dir, uefi=True):
    dist_dir = to_dist_dir(dist_name)
    @session_wrap.sudo
    def sudo_func(session):
        firewalld.configure(services=['dhcp', 'tftp', 'http'], add=True)(session)
        base_shell.run(session, f'mkdir -p {tftpboot_dir}')
        prepare_pxe_vmlinuz(session, dist_dir, www_iso_dir)
        ks_filename_list = kickstart.prepare_ks(session, pxe_ip, dist_dir)
        prepare_pxe_files(session)
        if uefi:
            grub_cfg_str = create_grub_cfg_str(dist_name, pxe_ip, dist_dir, ks_filename_list)
            prepare_pxe_uefi_files(session, grub_cfg_str)
        else:
            pxe_menu_str = create_pxe_menu_str(dist_name, pxe_ip, dist_dir, ks_filename_list)
            base_shell.run(session, f'mkdir -p {tftpboot_dir}/pxelinux.cfg')
            base_shell.here_doc(session, f'{tftpboot_dir}/pxelinux.cfg/default', pxe_menu_str.split('\n'))
    return sudo_func

def setup_pxe(dist_name, uefi=True):
    dist_dir = to_dist_dir(dist_name)
    def by_worker(session):
        pxe_ip = get_primary_ip(session)
        www_iso_dir = prepare_iso.prepare_dist_iso(dist_dir)(session)
        by_sudo_pxe(dist_name, pxe_ip, www_iso_dir, uefi)(session)
        from plur_linux.recipes.almalinux9 import docker
        docker.install(session)
        docker_tftpd.start()(session)
        docker_nginx.start()(session)
        docker_dhcpd.start(pxe_ip)(session)
    return by_worker

