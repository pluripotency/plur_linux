import re
from mini import misc
from plur import session_wrap
from plur import base_shell

keepalived_selinux_allowed_dir = '/usr/libexec/keepalived'


# this doesn't work, use add_rich_rule('vrrp') instead
# def commands_firewall_vrrp(interface):
#     """
#     >>> print('\\n'.join(commands_firewall_vrrp('eth0')))
#     firewall-cmd --direct --add-rule ipv4 filter INPUT 1 -i eth0 -d 224.0.0.18 -p vrrp -j ACCEPT
#     firewall-cmd --direct --add-rule ipv4 filter OUTPUT 1 -o eth0 -d 224.0.0.18 -p vrrp -j ACCEPT
#     firewall-cmd --runtime-to-permanent
#     firewall-cmd --direct --get-all-rules
#     """
#     rules = [
#         f'INPUT 1 -i {interface} -d 224.0.0.18 -p vrrp -j ACCEPT',
#         f'OUTPUT 1 -o {interface} -d 224.0.0.18 -p vrrp -j ACCEPT',
#     ]
#     commands = [f'firewall-cmd --direct --add-rule ipv4 filter {rule}' for rule in rules]
#     save_and_show = [
#         'firewall-cmd --runtime-to-permanent',
#         'firewall-cmd --direct --get-all-rules',
#     ]
#     return commands + save_and_show


def create_keepalived_conf_str(global_defs, vrrp_instance_list):
    """
    >>> gd = create_keepalived_smtp_conf()
    >>> vi_list = [create_keepalived_vrrp_instance_conf()]
    >>> print(create_keepalived_conf_str(gd, vi_list))
    global_defs {
        notification_email {
            notice@keepalived.local
        }
        notification_email_from notice@keepalived.local
        smtp_server 10.30.0.11
        smtp_connect_timeout 30
        router_id localhost
    }
    <BLANKLINE>
    vrrp_instance VI_1 {
        smtp_alert
        state BACKUP
        interface eth0
        virtual_router_id 32
        priority 100
        garp_master_delay 1
        nopreempt
        advert_int 1
        notify_master "/usr/libexec/keepalived/master.sh"
        notify_backup "/usr/libexec/keepalived/backup.sh"
        notify_fault  "/usr/libexec/keepalived/backup.sh"
        authentication {
            auth_type PASS
            auth_pass 4fa6ll@sd
        }
        virtual_ipaddress {
            192.168.10.254/24 dev eth0
        }
    }
    """
    gd = global_defs
    global_defs_str = f"""
    global_defs {{
        notification_email {{
            {gd['notification_email']}
        }}
        notification_email_from {gd['notification_email_from']}
        smtp_server {gd['smtp_server']}
        smtp_connect_timeout {gd['smtp_connect_timeout']}
        router_id {gd['router_id']}
    }}
    """
    conf_str = '\n'.join([line[4:] for line in global_defs_str.split('\n')[1:]])

    for vi in vrrp_instance_list:
        notify_master = ''
        if 'notify_master' in vi:
            notify_master = vi['notify_master']
        notify_backup = ''
        if 'notify_backup' in vi:
            notify_backup = vi['notify_backup']
        notify_fault = ''
        if 'notify_fault' in vi:
            notify_fault = vi['notify_fault']

        if 'nopreempt' in vi and vi['nopreempt'] is True:
            nopreempt = 'nopreempt'
        else:
            nopreempt = ''
        vip_list = ''
        for vip in vi['virtual_ipaddress']:
            vip_list += f"""
                {vip}"""
        vrrp_instance_str = f"""
        vrrp_instance {vi['instance_name']} {{
            smtp_alert
            state {vi['state']}
            interface {vi['interface']}
            virtual_router_id {vi['virtual_router_id']}
            priority {vi['priority']}
            garp_master_delay {vi['garp_master_delay']}
            {nopreempt}
            advert_int {vi['advert_int']}
            notify_master {notify_master}
            notify_backup {notify_backup}
            notify_fault  {notify_fault}
            authentication {{
                auth_type PASS
                auth_pass {vi['auth_pass']}
            }}
            virtual_ipaddress {{{vip_list}
            }}
        }}"""
        conf_str += '\n'.join([line[8:] for line in vrrp_instance_str.split('\n')])

    return conf_str


ex_gd = {
    'notification_email': 'notice@keepalived.local'
    , 'notification_email_from': 'notice@keepalived.local'
    , 'smtp_server': '10.30.0.11 25'
    , 'smtp_connect_timeout': 30
    , 'router_id': 'localhost'
}


def create_keepalived_smtp_conf(router_id='localhost', email='notice@keepalived.local', smtp_server='10.30.0.11 25'):
    gd = {
        'notification_email': email
        , 'notification_email_from': email
        , 'smtp_server': smtp_server
        , 'smtp_connect_timeout': 30
        , 'router_id': router_id
    }
    return gd


ex_vrrp_instance = {
    'instance_name': 'VI_1',
    'state': 'BACKUP',
    'interface': 'eth0',
    'virtual_router_id': 32,
    'priority': 100,
    'garp_master_delay': 1,
    'nopreempt': True,
    'advert_int': 1,
    'notify_master': f'{keepalived_selinux_allowed_dir}/master.sh',
    'notify_backup': f'{keepalived_selinux_allowed_dir}/backup.sh',
    'notify_fault':  f'{keepalived_selinux_allowed_dir}/backup.sh',
    'auth_pass': '4fa6ll@sd',
    'virtual_ipaddress': [
        '192.168.10.254/24 dev eth0'
    ]
}


def create_keepalived_vrrp_instance_conf(
    vrrp_instance_name='VI_1'
    , vrid=32
    , priority=100
    , auth_pass='4fa6ll@sd'
    , interface='eth0'
    , vip_list=['192.168.10.254/24 dev eth0']
    , notify_master=f'{keepalived_selinux_allowed_dir}/master.sh'
    , notify_backup=f'{keepalived_selinux_allowed_dir}/backup.sh'
    , notify_fault=f'{keepalived_selinux_allowed_dir}/backup.sh'
    , garp_master_delay=1
    , advert_int=1
):
    vi = {
        'instance_name': vrrp_instance_name,
        'state': 'BACKUP',
        'interface': interface,
        'virtual_router_id': vrid,
        'priority': priority,
        'garp_master_delay': garp_master_delay,
        'nopreempt': True,
        'advert_int': advert_int,
        'notify_master': f"{notify_master}",
        'notify_backup': f"{notify_backup}",
        'notify_fault': f"{notify_fault}",
        'auth_pass': auth_pass,
        'virtual_ipaddress': vip_list
    }
    return vi


def put_sample_scripts(session):
    base_shell.work_on(session, keepalived_selinux_allowed_dir)
    base_shell.here_doc(session, 'master.sh', misc.del_indent_lines("""
    #! /bin/bash
    echo "$HOSTNAME is master" > /tmp/ka_state.txt
    """))
    base_shell.here_doc(session, 'backup.sh', misc.del_indent_lines("""
    #! /bin/bash
    echo "$HOSTNAME is backup" > /tmp/ka_state.txt
    """))
    base_shell.run(session, 'chmod +x *.sh')


@session_wrap.sudo
def install_c7(session):
    from plur_linux.recipes import firewalld
    firewalld.install_if_not_exists(session)
    firewalld.add_rich_rule('vrrp')(session)

    put_sample_scripts(session)
    base_shell.yum_y_install([
        'keepalived'
    ])(session)


def configure_c7(gd, vi_list, backup_org_conf=False):
    @session_wrap.sudo
    def func(session):
        keepalived_conf_path = '/etc/keepalived/keepalived.conf'
        if backup_org_conf and not base_shell.check_file_exists(session, keepalived_conf_path + '.org'):
            base_shell.create_backup(session, keepalived_conf_path)

        keepalived_conf_str = create_keepalived_conf_str(gd, vi_list)
        base_shell.here_doc(session, keepalived_conf_path, keepalived_conf_str.split('\n'))
        base_shell.service_on(session, 'keepalived')

        # This is needed to wait keepalived start ONLY ON CONSOLE OF CentOS7
        # session.child.expect(r'\] IPVS: ipvs loaded.')

    return func


@session_wrap.sudo
def install_a8(session):
    from plur_linux.recipes import firewalld
    firewalld.install_if_not_exists(session)
    firewalld.add_rich_rule('vrrp')(session)

    put_sample_scripts(session)
    base_shell.run(session, 'dnf install -y keepalived')


def semanage_smtp(session, gd):
    if 'smtp_server' in gd:
        smtp_server = gd['smtp_server']
        if re.search('^' + misc.ipv4_exp_str + r'\s+\d{1,6}$' , smtp_server):
            smtp_server_port = re.split(r'\s+', smtp_server)[1].strip()
            if smtp_server_port != '25' and re.search(r'\d{1,6}', smtp_server_port):
                if not base_shell.check_command_exists(session, 'semanage'):
                    base_shell.run(session, 'dnf install -y policycoreutils-python-utils')
                # selinux: allow send mail to tcp port 1025, check by: semanage port -l | grep 1025
                # https://tex2e.github.io/blog/selinux/semanage-port
                base_shell.run(session, 'semanage port -a -t smtp_port_t -p tcp ' + smtp_server_port)


def configure_a8(gd, vi_list, backup_org_conf=False):
    @session_wrap.sudo
    def func(session):
        keepalived_conf_path = '/etc/keepalived/keepalived.conf'
        if backup_org_conf and not base_shell.check_file_exists(session, keepalived_conf_path + '.org'):
            base_shell.create_backup(session, keepalived_conf_path)

        semanage_smtp(session, gd)

        keepalived_conf_str = create_keepalived_conf_str(gd, vi_list)
        base_shell.here_doc(session, keepalived_conf_path, keepalived_conf_str.split('\n'))
        base_shell.service_on(session, 'keepalived')

    return func


@session_wrap.sudo
def install_a9(session):
    from plur_linux.recipes import firewalld
    firewalld.install_if_not_exists(session)
    firewalld.add_rich_rule('vrrp')(session)


    put_sample_scripts(session)
    base_shell.run(session, 'dnf install -y keepalived')


def configure_a9(gd, vi_list, backup_org_conf=False):
    @session_wrap.sudo
    def func(session):
        keepalived_conf_path = '/etc/keepalived/keepalived.conf'
        if backup_org_conf and not base_shell.check_file_exists(session, keepalived_conf_path + '.org'):
            base_shell.create_backup(session, keepalived_conf_path)

        semanage_smtp(session, gd)

        keepalived_conf_str = create_keepalived_conf_str(gd, vi_list)
        base_shell.here_doc(session, keepalived_conf_path, keepalived_conf_str.split('\n'))
        base_shell.run(session, f"restorecon -v '{keepalived_conf_path}'")
        base_shell.run(session, 'systemctl enable --now keepalived')

    return func


dict_keepalived = {
    'centos7': {
        'install': install_c7
        , 'configure': configure_c7
    },
    'almalinux8': {
        'install': install_a8
        , 'configure': configure_a8
    },
    'almalinux9': {
        'install': install_a9
        , 'configure': configure_a9
    }
}
