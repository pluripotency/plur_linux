from plur import base_shell
from plur.base_shell import create_sequence
from plur.output_methods import waitprompt, success, send_line, send_pass, get_pass, wait, success_f, send_line_f, send_pass_f
from mini.menu import *
import re


def console(vm):
    def wrap(func):
        def on_console(session=None):
            success_console_run = False
            if console_start(session, vm):
                func(session)
                console_logout(session)
                session.pop_node()
                console_exit(session)
                success_console_run= True
            return success_console_run
        return on_console
    return wrap


def console_login(kvm, vm, start_action):
    def func(session):
        if re.search('^ubuntu', vm.platform):
            login_rows = [
                ['(' + vm.hostname + '|localhost|ubuntu) login: ', send_line_f(vm.username)],
                ['Password: ', send_pass_f(vm.password)],
                [kvm.waitprompt, success_f(False)],
                [vm.waitprompt, success_f(True)],
            ]
        else:
            login_rows = [
                ['(' + vm.hostname + '|localhost|ubuntu) login: ', wait([
                    ['Password: ', wait([
                        [kvm.waitprompt, success_f(False)],
                        [vm.waitprompt, success_f(True)],
                    ], send_pass_f(vm.password))]
                ], send_line_f(vm.username))],
                [kvm.waitprompt, success_f(False)],
                [vm.waitprompt, success_f(True)],
            ]
        rows = [
            [r'Escape character is \^\]', wait(login_rows, send_line_f(''))],
            ['error: failed to get domain', wait([
                [kvm.waitprompt, success_f(False)],
            ])]
        ]

        session.child.delaybeforesend = 0.3
        session.set_timeout(600)
        result = session.do(create_sequence(start_action, rows))
        session.child.delaybeforesend = 0
        session.set_timeout()
        if result:
            session.push_node(vm)
            base_shell.platform_run(session)
        return result
    return func


def console_login_cloud_init(kvm, vm, start_action):
    def func(session):
        login_rows = [
            ['(' + vm.hostname + '|localhost|ubuntu) login: ', wait([
                ['Password: ', wait([
                    [kvm.waitprompt, success_f(False), ''],
                    [vm.waitprompt, success_f(True), ''],
                ], send_pass_f(vm.password)), '']
        ], send_line_f(vm.username)), ''],
            [kvm.waitprompt, success_f(False), ''],
            [vm.waitprompt, success_f(True), ''],
        ]

        cloud_init_rows = [
            ['Cloud-init v.+Datasource.+seconds', wait(login_rows, send_line_f('')), '']
        ]
        session.set_timeout(600)
        result = session.do(create_sequence(start_action, [
            [r'Escape character is \^\]', wait(cloud_init_rows, send_line_f('')), ''],
            ['error: failed to get domain', wait([
                [kvm.waitprompt, success_f(False), ''],
            ]), '']
        ]))
        session.set_timeout()
        if result:
            session.push_node(vm)
        return result
    return func


def console_start(session, vm):
    kvm = session.nodes[-1]
    return console_login(kvm, vm, 'sudo virsh console %s' % vm.hostname)(session)


def shutdown_from_console(session):
    action = 'sudo shutdown -h now'
    rows = [
        ['] Removed ', success, None, 'Shutdown from console.'],
        ['Shutting down', success, None, 'Shutdown from console.'],
        ['The system is going down for halt NOW', success, None, 'Power down.'],
        [r'Power down\.', success, None, 'Power down.'],
        [r'Powering off\.', success, None, 'Shutdown from console.'],
        ['Show Plymouth Power Off Screen', success, None, 'Reboot from console.'],
    ]
    session.do(create_sequence(action, rows))
    console_exit(session)


def shutdown_from_kvm(session, vm_hostname):
    def wait_vm_shutdown(sess, hostname):
        import re
        import time
        time.sleep(1)
        action = "virsh list --all | grep ' %s '" % hostname
        if re.search('shut off', base_shell.run(sess, action)):
            base_shell.run(sess, '')
            time.sleep(1)
            return
        wait_vm_shutdown(sess, hostname)

    base_shell.run(session, f'sudo virsh shutdown {vm_hostname}')
    wait_vm_shutdown(session, vm_hostname)


def reboot_from_console(session):
    action = 'sudo reboot'
    rows = [['Shutting down', success, None, 'Reboot from console.']]
    rows += [[r'Rebooting\.', success, None, 'Reboot from console.']]
    rows += [['Show Plymouth Reboot Screen', success, None, 'Reboot from console.']]
    session.do(create_sequence(action, rows))
    console_exit(session)


def reboot_from_kvm(session, vm_hostname):
    base_shell.run(session, f'virsh reboot {vm_hostname}')


def console_logout(session):
    rows = [
        ['logout\n.+ login: ', success, None, 'logout']
        , ['logout', success, None, 'logout']
    ]
    session.do(create_sequence('exit', rows))


def console_exit(session):
    session.do(create_sequence(']', [
        ['.+@.+[$#] ', success, None, 'Console Exit succeeded.'],
        ['', waitprompt, None, 'Console Exit succeeded.']
    ], 'sendcontrol'))


def define(session, vmname):
    base_shell.run(session, f'virsh define {vmname}.xml')


def dumpxml(session, vmname, xml_dir):
    base_shell.run(session, f'virsh dumpxml {vmname} > {xml_dir}/{vmname}.xml')


def reset(session, vmname):
    session.do(create_sequence(f'virsh reset {vmname}', [
        [f"Domain '?{vmname}'? was reset(\r\n|\n)", success, None, ''],
    ]))
    session.child.expect(session.waitprompt)


def start(session, vmname):
    session.do(create_sequence(f'virsh start {vmname}', [
        [f"Domain '?{vmname}'? started(\r\n|\n)", success, None, ''],
        ['error: Domain is already active(\r\n|\n)', success, None, ''],
    ]))
    session.child.expect(session.waitprompt)


def shutdown(session, vmname):
    action = f'virsh shutdown {vmname}'
    successcase = f'Domain {vmname} is being shutdown(\r\n|\n)'
    rows = [[successcase, waitprompt, None, successcase]]
    session.do(create_sequence(action, rows))
    session.child.expect(session.waitprompt)


def destroy(session, vmname):
    base_shell.run(session, f'virsh destroy {vmname}')


def attach_vdisk(session, vmname, vdisk_path, diskformat='qcow2', dev_name='vda', offline=False):
    action = f'virsh attach-disk {vmname} {vdisk_path} {dev_name} --subdriver {diskformat} --cache none'
    if offline:
        action += ' --config'

    capture = base_shell.run(session, action)
    if re.search('error: ', capture):
        print(red('error in attach-device'))
        print(red(capture))
        exit(1)
    else:
        return True


def attach_cdrom(session, vmname, iso_file, vdisk_name='hdb', offline=False):
    xml = f"""
    <disk type='file' device='cdrom'>
      <driver name='qemu' type='raw'/>
      <source file='{iso_file}'/>
      <target dev='{vdisk_name}' bus='ide'/>
      <readonly/>
      <address type='drive' controller='0' bus='0' target='0' unit='1'/>
    </disk>
    """
    xml_filepath = '/etc/libvirt/qemu/cdrom.xml'
    base_shell.here_doc(session, xml_filepath, xml.split('\n')[1:])
    action = f'virsh attach-device {vmname} {xml_filepath}'
    if offline:
        action += ' --config'
    base_shell.run(session, action)


def attach_vnet(session, vmname, vnetxml, offline=False):
    action = f'virsh attach-device {vmname} {vnetxml}'
    if offline:
        action += ' --config'

    capture = base_shell.run(session, action)

    if re.search('error: ', capture):
        print(red('error in attach-device'))
        print(red(capture))
        exit(1)
    else:
        return True


def migrate_storageinc(session, vmname, kvmname):
    action = 'virsh migrate --live --copy-storage-inc ' + \
            '%s qemu+ssh://%s/system --persistent --verbose' % (vmname, kvmname)
    rows = login_rows()
    return session.do(create_sequence(action, rows))


def is_running(session, vmname):
    action = "virsh list --all|grep '%s '|awk '{ print $3 }'" % vmname
    rows = [['running', success, True, '%s is running' % vmname]]
    rows += [['shut',   success, False, '%s seems not running' % vmname]]
    result = session.do(create_sequence(action, rows))
    session.child.expect(session.waitprompt)
    return result


def login_rows():
    rows = [
        [r'Are you sure you want to continue connecting \(yes/no\)\?', send_line, 'yes'],
        ["[Pp]assword:", send_pass, None],
        ["Permission denied, please try again.+password:", get_pass, None],
        [r"Permission denied \(publickey,", 'exit', ''],
        ["ssh: Could not resolve hostname", 'exit', ''],
        ["ssh: connect to host ", 'exit', ''],
        ['', waitprompt, '']
    ]
    return rows
