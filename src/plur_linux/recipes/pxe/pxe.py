from mini import misc
from mini import ansi_colors
from plur import session_wrap
from plur import base_shell
from recipes import firewalld
from recipes.pxe import dhcpd
from recipes.pxe import httpd
from recipes.pxe import kickstart
from recipes.pxe import prepare_iso
import re


def start_tftp_server(session):
    base_shell.run(session, 'dnf install -y tftp-server')
    base_shell.run(session, 'systemctl enable --now tftp.socket')


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
    value += misc.del_indent(f"""
    label local
      menu label Boot from ^local drive
      localboot 0xffff

    """)
    return value


def prepare_pxe_files(session, pxe_menu_contets_str, tftpboot_dir='/var/lib/tftpboot'):
    [base_shell.run(session, a) for a in [
        'dnf -y install syslinux'
        , rf'\cp -f /usr/share/syslinux/pxelinux.0 {tftpboot_dir}/'
        , r'\cp -f /usr/share/syslinux/{menu.c32,vesamenu.c32,ldlinux.c32,libcom32.c32,libutil.c32} ' + f'{tftpboot_dir}/'
        , f'mkdir {tftpboot_dir}/pxelinux.cfg'
    ]]
    base_shell.here_doc(session, '/var/lib/tftpboot/pxelinux.cfg/default', pxe_menu_contets_str.split('\n'))


def prepare_pxe_vmlinuz(session, dist_dir, tftpboot_dir='/var/lib/tftpboot'):
    base_shell.run(session, f'mkdir {tftpboot_dir}/{dist_dir}')
    base_shell.run(session, rf'\cp -f /var/pxe/{dist_dir}/images/pxeboot/' + '{vmlinuz,initrd.img}' + f' {tftpboot_dir}/{dist_dir}/')


def prepare_pxe_uefi_files(session, grub_cfg_str):
    base_shell.work_on(session, '/root/rpm')
    # base_shell.run(session, 'dnf -y install --downloadonly --downloaddir=/root/rpm shim grub2-efi-x64')
    base_shell.run(session, 'dnf download shim grub2-efi-x64')
    [base_shell.run(session, a) for a in misc.del_indent_lines(r"""
    rpm2cpio shim-x64-*.rpm | cpio -dimv
    rpm2cpio grub2-efi-x64-*.rpm | cpio -dimv
    \cp -f ./boot/efi/EFI/BOOT/BOOTX64.EFI /var/lib/tftpboot/
    \cp -f ./boot/efi/EFI/almalinux/grubx64.efi /var/lib/tftpboot/
    chmod 644 /var/lib/tftpboot/{BOOTX64.EFI,grubx64.efi}
    """)]
    base_shell.here_doc(session, '/var/lib/tftpboot/grub.cfg', grub_cfg_str.split('\n'))


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


def setup_pxe_base(pxe_ip, dist_dir, www_iso_dir):
    if re.search(r'^192\.168\.0\.', pxe_ip):
        subnet_params = {
            'subnet': '192.168.0.0',
            'netmask': '255.255.255.0',
            'gateway': '192.168.0.1',
            'nameservers': '8.8.8.8',
            'dh_range': '192.168.0.200 192.168.0.250',
            'broadcast': '192.168.0.255',
        }
        allowed_net = '192.168.0.0/24'
    else:
        subnet_params = {
            'subnet': '192.168.10.0',
            'netmask': '255.255.255.0',
            'gateway': '192.168.10.62',
            'nameservers': '192.168.10.1',
            'dh_range': '192.168.10.200 192.168.10.250',
            'broadcast': '192.168.10.255',
        }
        allowed_net = '192.168.10.0/24'
    http_params = {
        'file_name': 'pxeboot.conf',
        'alias': f'/{dist_dir}',
        'dir_path': www_iso_dir,
        'allowed_net': allowed_net
    }

    @session_wrap.sudo
    def func(session):
        firewalld.configure(services=['dhcp', 'tftp', 'http'], add=True)(session)
        start_tftp_server(session)
        dhcpd.setup(subnet_params, set_fw=False, pxe_ip=pxe_ip)(session)
        httpd.setup(set_fw=False, http_params=http_params)(session)

    return func


def get_primary_ip(session):
    primary_ip = None
    for line in base_shell.run(session, 'ip -4 -br a').splitlines():
        if not primary_ip and re.search('^eth', line):
            primary_ip = re.split(r'\s+', line)[2].split('/')[0]
    if not primary_ip:
        print(ansi_colors.red("Couldn't get pxe_ip"))
        exit(1)
    return primary_ip


def setup_a8_pxe_uefi(session):
    dist_name = 'AlmaLinux 8'
    pxe_ip = get_primary_ip(session)
    dist_dir, www_iso_dir = prepare_iso.prepare_a8_iso(session)
    setup_pxe_base(pxe_ip, dist_dir, www_iso_dir)(session)

    @session_wrap.sudo
    def sudo_func(session):
        prepare_pxe_vmlinuz(session, dist_dir)
        ks_filename_list = kickstart.prepare_ks(session, pxe_ip, dist_dir)
        pxe_menu_str = create_pxe_menu_str(dist_name, pxe_ip, dist_dir, ks_filename_list)
        prepare_pxe_files(session, pxe_menu_str)
        grub_cfg_str = create_grub_cfg_str(dist_name, pxe_ip, dist_dir, ks_filename_list)
        prepare_pxe_uefi_files(session, grub_cfg_str)

    sudo_func(session)


def setup_a8_pxe(session):
    pxe_ip = get_primary_ip(session)
    dist_dir, www_iso_dir = prepare_iso.prepare_a8_iso(session)
    setup_pxe_base(pxe_ip, dist_dir, www_iso_dir)(session)

    @session_wrap.sudo
    def sudo_func(session):
        prepare_pxe_vmlinuz(session, dist_dir)
        ks_filename_list = kickstart.prepare_ks(session, pxe_ip, dist_dir)
        pxe_menu_str = create_pxe_menu_str('AlmaLinux 8', pxe_ip, dist_dir, ks_filename_list)
        prepare_pxe_files(session, pxe_menu_str)

    sudo_func(session)


def setup_a9_pxe_uefi(session):
    dist_name = 'AlmaLinux 9'
    pxe_ip = get_primary_ip(session)
    dist_dir, www_iso_dir = prepare_iso.prepare_a9_iso(session)
    setup_pxe_base(pxe_ip, dist_dir, www_iso_dir)(session)

    @session_wrap.sudo
    def sudo_func(session):
        prepare_pxe_vmlinuz(session, dist_dir)
        ks_filename_list = kickstart.prepare_ks(session, pxe_ip, dist_dir)
        pxe_menu_str = create_pxe_menu_str(dist_name, pxe_ip, dist_dir, ks_filename_list)
        prepare_pxe_files(session, pxe_menu_str)
        grub_cfg_str = create_grub_cfg_str(dist_name, pxe_ip, dist_dir, ks_filename_list)
        prepare_pxe_uefi_files(session, grub_cfg_str)

    sudo_func(session)


def setup_a9_pxe(session):
    pxe_ip = get_primary_ip(session)
    dist_dir, www_iso_dir = prepare_iso.prepare_a9_iso(session)
    setup_pxe_base(pxe_ip, dist_dir, www_iso_dir)(session)

    @session_wrap.sudo
    def sudo_func(session):
        prepare_pxe_vmlinuz(session, dist_dir)
        ks_filename_list = kickstart.prepare_ks(session, pxe_ip, dist_dir)
        pxe_menu_str = create_pxe_menu_str('AlmaLinux 9', pxe_ip, dist_dir, ks_filename_list)
        prepare_pxe_files(session, pxe_menu_str)

    sudo_func(session)

