#! /usr/bin/env python
from plur import base_shell
from plur import session_wrap
from plur.ansi_colors import *


def install_libguestfs(session):
    base_shell.yum_install(session, {'packages': [
        'libguestfs',
        'libguestfs-tools',
        'libguestfs-tools-c',
        'virt-install',
    ]})


def install_kvm(session):
    base_shell.yum_install(session, {'packages': [
        'qemu-kvm',
        'libvirt',
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


@session_wrap.sudo
def ip_on_prompt(session):
    script = """
if [ ! -f /etc/issue.org ]; then
    /bin/cp /etc/issue /etc/issue.org
fi
/bin/cp -f /etc/issue.org /etc/issue
/sbin/ip -4 a | grep -v 'host lo' | /bin/awk '/inet / {print $2}' >> /etc/issue
"""
    base_shell.here_doc(session, '/etc/rc.d/rc.local', script.split('\n'))


def run_command_in_builder(auth_keys_url='http://192.168.10.14:4000/static/keys'):
    command = """ --run-command '
    set -eux
    mkdir -p /root/.ssh/pub
    chmod 700 /root/.ssh
    curl %s > /root/.ssh/authorized_keys
    chmod 600 /root/.ssh/authorized_keys
' \\
--firstboot-command '
    restorecon -RFv /root/.ssh/
'

""" % auth_keys_url
    return command


def virt_builder(guest_os, guest_volume_path, image_format, root_password, command=None):
    builder = [
        'virt-builder ' + guest_os,
        '-o ' + guest_volume_path,
        '--format ' + image_format,
        '--arch x86_64',
        '--root-password password:' + root_password,
        '--timezone Asia/Tokyo',
    ]
    if command:
        builder.append(command)
    return ' '.join(builder)


def virt_install(guest_name, image_format, image_dir):
    command = """virt-install \\
  --name %s \\
  --disk path=%s,format=%s \\
   \\
  --network network=default \\
  --hvm --virt-type kvm \\
  --vcpus 1 --ram 1024 --arch x86_64 \\
  --os-type linux --os-variant rhel7 \\
  --boot hd --graphics none --serial pty --console pty \\
  --import --noreboot
    """ % (guest_name, image_dir + guest_name + '.' + image_format, image_format)
    return command


def virt_sysprep(guest_volume_path):
    """
    remove unneeded
    virt-sysprep --list-operations
    """
    # return 'virt-sysprep -d %s --operations defaults,-ssh-userdir' % guest_volume_path
    return 'virt-sysprep -d %s --operations defaults' % guest_volume_path


def virt_filesystems(image_path):
    return "virt-filesystems --long --parts --blkdevs -h -a %s" % image_path


def show_image_filesystems(image):
    return lambda session: base_shell.run(session, virt_filesystems(image))


def virt_customize_str(guest_name, ip_params):
    ip = ip_params['ip']
    gw = ip_params['gw']
    dns = ip_params['dns']

    action = """virt-customize -d %s --hostname %s --firstboot-command '
    nmcli con modify eth0 \\
      connection.autoconnect yes \\
      ipv4.method manual \\
      ipv4.addresses %s \\
      ipv4.gateway %s \\
      ipv4.dns %s
    nmcli con up eth0
  '
    """ % (guest_name, guest_name, ip, gw, dns)
    return action


def virt_customize(image_path, args):
    def func(session):
        virt_customize_cmd = 'virt-customize'
        if not base_shell.check_command_exists(session, virt_customize_cmd):
            install_libguestfs(session)
        base_shell.run(session, " ".join([
            virt_customize_cmd,
            '-a',
            image_path
        ] + args))
    return func


def create_base_guest(root_password, image_format, work_dir='$HOME/virt-builder/', sshkey_url=None):
    def func(session):
        guest_os = 'centos-7.4'
        base_guest_name = 'centos74_base'
        base_guest_volume_path = work_dir + base_guest_name + '.' + image_format

        base_shell.work_on(session, work_dir)
        if not base_shell.check_file_exists(session, base_guest_volume_path):
            command = None
            if sshkey_url:
                command = run_command_in_builder(sshkey_url)
            actions = [
                virt_builder(guest_os, base_guest_volume_path, image_format, root_password, command=command),
                virt_install(base_guest_name, image_format, work_dir),
                virt_sysprep(base_guest_name),
                'virsh undefine ' + base_guest_name,
                ]
            [base_shell.run(session, a) for a in actions]
        return base_guest_volume_path
    return func


def resize_qcow2_from(source_image_path, guest_name, disk_size=8, dev_path='/dev/sda1', work_dir='$HOME/Downloads/vm/'):
    """
    run with user right, no root required
    virt-filesystems -a devname -hl
    """
    def func(session):
        guest_qcow2 = guest_name + '.qcow2'
        disk_size_str = str(disk_size) + 'G'

        base_shell.work_on(session, work_dir)
        actions = [
            virt_filesystems(source_image_path),
            'qemu-img create -f qcow2 -o preallocation=metadata %s %s' % (guest_qcow2, disk_size_str),
            'virt-resize --expand %s %s %s' % (dev_path, source_image_path, guest_qcow2)
        ]
        [base_shell.run(session, a) for a in actions]
        return work_dir + guest_qcow2

    return func


def setup(session):
    work_dir = '$HOME/Downloads/vm/'
    guest_name = 'c7guest'
    image_format = 'qcow2' #raw/qcow2
    base_guest_volume_path = create_base_guest('password', image_format, work_dir)(session)
    guest_path = resize_qcow2_from(base_guest_volume_path, guest_name, disk_size=16, dev_path='/dev/sda3', work_dir=work_dir)(session)

    vm_dir = '/vm_images/'
    base_shell.run(session, 'sudo mv %s %s' % (guest_path, vm_dir))

    @session_wrap.sudo
    def start_guest(session):
        ip_params = {
            'ip': '192.168.10.81/24',
            'gw': '192.168.10.62',
            'dns': '192.168.10.23,192.168.10.61'
        }
        actions = [
            'virsh destroy %s' % guest_name,
            'virsh undefine %s' % guest_name,
            virt_install(guest_name, image_format, vm_dir),
            virt_customize_str(guest_name, ip_params)
        ]
        [base_shell.run(session, a) for a in actions]
    start_guest(session)

