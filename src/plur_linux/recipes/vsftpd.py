from plur import base_shell
from plur import session_wrap
from plur_linux.recipes import firewalld


@session_wrap.sudo
def vsftpd_server_setup(session):
    base_shell.yum_y_install(['vsftpd'])(session)

    vsftpd_dir = '/etc/vsftpd'
    chroot_user = 'worker'
    base_shell.run(session, f'echo {chroot_user} > {vsftpd_dir}/chroot_list')

    conf_file_path = f'{vsftpd_dir}/vsftpd.conf'
    if not base_shell.check_file_exists(session, f'{conf_file_path}.org'):
        base_shell.create_backup(session, conf_file_path)
    base_shell.sed_pipe(session, f'{conf_file_path}.org', conf_file_path, [
        [
            'anonymous_enable=YES',
            'anonymous_enable=NO',
        ],
        [
            '#ascii_upload_enable=YES',
            'ascii_upload_enable=YES',
        ],
        [
            '#ascii_download_enable=YES',
            'ascii_download_enable=YES',
        ],
        [
            '#chroot_local_user=YES',
            'chroot_local_user=YES',
        ],
        [
            '#chroot_list_enable=YES',
            'chroot_list_enable=YES',
        ],
        [
            '#chroot_list_file=/etc/vsftpd/chroot_list',
            'chroot_list_file=/etc/vsftpd/chroot_list',
        ],
        [
            '#ls_recurse_enable=YES',
            'ls_recurse_enable=YES',
        ],
        [
            'listen=NO',
            'listen=YES',
        ],
        [
            'listen_ipv6=YES',
            'listen_ipv6=NO',
        ],
    ])
    [base_shell.run(session, f'echo {line} >> {conf_file_path}') for line in [
        # 'local_root=public_html',
        'use_localtime=YES',
        'seccomp_sandbox=NO',
    ]]
    base_shell.run(session, 'setsebool -P ftpd_full_access on')

    firewalld.configure(['ftp'], add=True)(session)
    base_shell.service_on(session, 'vsftpd')


def run_ftp_client(session):
    user = 'worker'
    password = 'worker'
    server_ip = '192.168.0.1'
    get_file = 'test.txt'
    if not base_shell.check_command_exists(session, 'lftp'):
        base_shell.yum_y_install(['lftp'])(session)
    command = f"lftp -u {user},{password} {server_ip} -e 'get {get_file};exit'"
    base_shell.run(session, command)


dict_vsftpd = {
    'centos7': {
        'package': vsftpd_server_setup
    },
    'almalinux8': {
        'package': vsftpd_server_setup
    },
}

