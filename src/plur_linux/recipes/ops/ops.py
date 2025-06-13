from plur import base_shell
from plur import session_wrap
from plur_linux.recipes.centos import chrony
from plur_linux.recipes import firewalld
from mini import misc


def set_hostname(hostname):
    @session_wrap.sudo
    def func(session):
        platform = session.nodes[-1].platform
        if platform == 'centos6':
            actions = [
                f'hostname {hostname}',
                f'echo HOSTNAME={hostname} > /etc/sysconfig/network.tmp',
                'cat /etc/sysconfig/network |grep -v HOSTNAME >> /etc/sysconfig/network.tmp',
                'mv /etc/sysconfig/network.tmp /etc/sysconfig/network',
            ]
        else:
            actions = [f'hostnamectl set-hostname {hostname}']
        [base_shell.run(session, a) for a in actions]
    return func


def set_timezone(timezone='Asia/Tokyo'):
    @session_wrap.sudo
    def func(session):
        platform = session.nodes[-1].platform
        if platform == 'centos6':
            [base_shell.run(session, a) for a in [
                f'echo ZONE="{timezone}" > /etc/sysconfig/clock',
                'echo UTC="false" >> /etc/sysconfig/clock',
                'source /etc/sysconfig/clock',
                rf'\cp -f /usr/share/zoneinfo/{timezone} /etc/localtime',
            ]]
        else:
            base_shell.run(session, f'timedatectl set-timezone {timezone}')
    return func


def set_keymap(keymap='jp106'):
    @session_wrap.sudo
    def func(session):
        base_shell.run(session, f'localectl set-keymap {keymap}')
    return func


@session_wrap.sudo
def remove_cockpit(session):
    if base_shell.check_dir_exists(session, '/etc/cockpit'):
        [base_shell.run(session, a) for a in misc.del_indent_lines("""
        systemctl stop cockpit
        rpm -e cockpit-system
        rpm -e cockpit-bridge
        rpm -e cockpit-ws
        rm -R -f /run/cockpit
        rm -R -f /etc/cockpit
        rm -R -f /usr/share/cockpit
        rm -R -f /var/lib/selinux/targeted/active/modules/100/cockpit
        rm -R -f /usr/share/selinux/targeted/default/active/modules/100/cockpit
        """)]


def create_hosts(host_list):
    # host_list = [
    #     [ip, hostname1, hostname2],
    #     [ip, hostname1],
    # ]
    @session_wrap.sudo
    def f(session):
        hosts_path = '/etc/hosts'
        base_shell.create_backup(session, hosts_path)
        base_shell.run(session, f'\\cp -f {hosts_path}.org {hosts_path}')
        host_entries = ['    '.join(host) for host in host_list]
        [base_shell.run(session, f'echo "{host_entry}" >> {hosts_path}') for host_entry in host_entries]
    return f


def idempotent_append_egrep_str(file_path, expression, line):
    return f'egrep -q "{expression}" {file_path} || echo "{line}" >> {file_path}'


def idempotent_append_hosts(host_list):
    # host_list = [
    #     [ip, hostname1, hostname2],
    #     [ip, hostname1],
    # ]
    @session_wrap.sudo
    def func(session):
        hosts_path = '/etc/hosts'
        for ip_hostname in host_list:
            ip = ip_hostname[0]
            first_host = ip_hostname[1]
            host_entry_expression = rf'{ip}(\s|\t)+{first_host}'
            host_entry = f'{ip} {first_host}'
            if len(ip_hostname) > 2:
                for host in ip_hostname[2:]:
                    host_entry += ' ' + host
            base_shell.run(session, idempotent_append_egrep_str(hosts_path, host_entry_expression, host_entry))
    return func


def service_on(service):
    @session_wrap.sudo
    def func(session):
        platform = session.nodes[-1].platform
        if platform == 'centos6':
            action = f'chkconfig {service} on && service {service} start'
        else:
            action = f'systemctl enable {service} && systemctl restart {service}'
        base_shell.run(session, action)
    return func


def service_off(service):
    @session_wrap.sudo
    def func(session):
        platform = session.nodes[-1].platform
        if platform == 'centos6':
            action = f'chkconfig {service} off && service {service} stop'
        else:
            action = f'systemctl disable {service} && systemctl stop {service}'
        base_shell.run(session, action)
    return func


def set_selinux(mode='disabled'):
    @session_wrap.sudo
    def func(session):
        mode_list = [
            ['disabled', 0],
            ['permissive', 0],
            ['enforcing', 1],

        ]
        mode_num = None
        for item in mode_list:
            if mode == item[0]:
                mode_num = item[1]
        if mode_num is None:
            misc.err_exit('err in set_selinux: no such mode:' + mode)
        file_path = '/etc/selinux/config'
        base_shell.run(session, f'setenforce {mode_num}')
        base_shell.run(session, f'sed -i -E "s/^SELINUX=.*$/SELINUX={mode}/g" {file_path}')
    return func


def disable_selinux(session):
    set_selinux()(session)


def permissive_selinux(session):
    set_selinux('permissive')(session)


def enforce_selinux(session):
    set_selinux('enforcing')(session)


@session_wrap.sudo
def disable_ipv6(session):
    conf = '/etc/sysctl.d/disable_ipv6.conf'
    if not base_shell.check_file_exists(session, conf):
        base_shell.run(session, 'echo "net.ipv6.conf.all.disable_ipv6=1" > ' + conf)
        base_shell.run(session, 'echo "net.ipv6.conf.default.disable_ipv6=1" >> ' + conf)
        base_shell.run(session, 'sysctl -p ' + conf)


@session_wrap.sudo
def increase_inotify_max_user_watches(session):
    sysctl_line = 'fs.inotify.max_user_watches=100000'
    base_shell.idempotent_append(session, '/etc/sysctl.conf', sysctl_line, sysctl_line)
    base_shell.run(session, 'sysctl -p')


def mkswap(size_gig=1):
    @session_wrap.sudo
    def func(session):
        swap_file_path = '/swapfile'
        if not base_shell.check_file_exists(session, swap_file_path):
            [base_shell.run(session, a) for a in [
                f'dd if=/dev/zero of={swap_file_path} bs=1M count={size_gig * 1024}'
                , f'mkswap {swap_file_path}'
                , f'chmod 600 {swap_file_path}'
                , f'swapon {swap_file_path}'
                , f'swapon -s'
            ]]
            swap_file_line = f'{swap_file_path}    swap    swap    defaults 0 0'
            base_shell.idempotent_append(session, '/etc/fstab', swap_file_line, swap_file_line)
    return func


@session_wrap.sudo
def c7base_just_update(session):
    disable_ipv6(session)
    session.set_timeout(1800)
    base_shell.run(session, 'yum update -y')
    # yum clean all causes long time to init yum operation
    # base_shell.run(session, 'dnf clean all')
    session.set_timeout()


@session_wrap.sudo
def c7base_update(session):
    c7base_just_update(session)
    if not base_shell.check_command_exists(session, 'tmux'):
        disable_selinux(session)
        base_shell.run(session, 'dnf install -y ' + ' '.join([
            'vim'
            , 'tmux'
            , 'git'
            , 'bind-utils'
            , 'dstat'
            , 'glusterfs-fuse'
        ]))
        chrony.configure(session)
        firewalld.configure(services=['ssh'], add=True)


