from mini import misc
from plur import base_shell
from plur import output_methods
bin_path = 'build/cargo_target/x86_64-unknown-linux-musl/debug'

"""
https://dev.classmethod.jp/articles/reinvent2018-running-firecracker-on-premises/
"""

def install_from_git(work_dir):
    def run(session):
        base_shell.work_on(session, work_dir, is_file_path=True)
        [base_shell.run(session, a) for a in [
            'git clone https://github.com/firecracker-microvm/firecracker',
            'cd firecracker',
        ]]
        base_shell.create_sequence('tools/devtool build', [
            ['Continue\? \(y/n)', output_methods.send_line, 'y'],
            ['', output_methods.waitprompt, ''],
        ])
        [base_shell.run(session, a) for a in [
            f'cd {bin_path}',
            'ls -l firecracker',
        ]]
        actions = misc.del_indent_lines("""
        sudo apt-get install -y acl
        curl -fsSL -o hello-vmlinux.bin https://s3.amazonaws.com/spec.ccfc.min/img/hello/kernel/hello-vmlinux.bin
        curl -fsSL -o hello-rootfs.ext4 https://s3.amazonaws.com/spec.ccfc.min/img/hello/fsfiles/hello-rootfs.ext4
        """)
        [base_shell.run(session, a) for a in actions]
    return run


def install_binary(work_dir):
    def run(session):
        base_shell.work_on(session, work_dir)

        actions = misc.del_indent_lines("""
        sudo apt-get install -y acl
        latest=$(basename $(curl -fsSLI -o /dev/null -w  %{url_effective} https://github.com/firecracker-microvm/firecracker/releases/latest))
        curl -LOJ https://github.com/firecracker-microvm/firecracker/releases/download/${latest}/firecracker-${latest}-$(uname -m) 
        mv firecracker-${latest}-$(uname -m) firecracker
        chmod +x firecracker
        curl -fsSL -o hello-vmlinux.bin https://s3.amazonaws.com/spec.ccfc.min/img/hello/kernel/hello-vmlinux.bin
        curl -fsSL -o hello-rootfs.ext4 https://s3.amazonaws.com/spec.ccfc.min/img/hello/fsfiles/hello-rootfs.ext4
        """)
        [base_shell.run(session, a) for a in actions]
    return run


def install(session):
    from .kvm import install as kvm_install
    kvm_install(session)

    work_dir = '$HOME/Projects/firecracker'
    install_binary(work_dir)(session)


def start_api(session):
    actions = misc.del_indent_lines("""
    sudo setfacl -m u:${USER}:rw /dev/kvm
    rm -f /tmp/firecracker.socket
    ./firecracker --api-sock /tmp/firecracker.socket
    """)
    [base_shell.run(session, a) for a in actions]


def start_vm_by_api(session):
    actions = misc.del_indent_lines("""
    curl --unix-socket /tmp/firecracker.socket -i \
    -X PUT 'http://localhost/boot-source' \
    -H 'Accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{"kernel_image_path": "./hello-vmlinux.bin", "boot_args": "console=ttyS0 reboot=k panic=1 pci=off"}'

    curl --unix-socket /tmp/firecracker.socket -i \
    -X PUT 'http://localhost/drives/rootfs' \
    -H 'Accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{"drive_id": "rootfs", "path_on_host": "./hello-rootfs.ext4", "is_root_device": true, "is_read_only": false}'

    curl --unix-socket /tmp/firecracker.socket -i \
    -X PUT 'http://localhost/actions' \
    -H  'Accept: application/json' \
    -H  'Content-Type: application/json' \
    -d '{ "action_type": "InstanceStart" }'
    """)
    [base_shell.run(session, a) for a in actions]


if __name__ == "__main__":
    from plur import session_wrap
    from plur import base_node

    password = input('password: ')
    node = base_node.Linux('udocker', password=password, platform='ubuntu')
    node.access_ip = '192.168.122.20'

    work_dir = '$HOME/Projects/firecracker'
    # for git installed
    # work_dir = work_dir + '/' + bin_path

    @session_wrap.ssh(node)
    def start_vm(session):
        base_shell.work_on(session, work_dir)
        start_vm_by_api(session)

    start_vm()

