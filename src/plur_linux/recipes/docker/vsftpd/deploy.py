import os
import re
from mini import misc
from plur import session_wrap
from plur import base_shell
from recipes.ops import ssh


def scp_docker_image(dst_path, password):
    def func(session):
        src_path = '/mnt/MC/work_space/archives/docker-images/fauria_vsftpd.tar.gz'
        ssh.scp(session, src_path, dst_path, password)
    return func


def create_start_sh(pasv_ip, username='ftpclient', password='ftpclient'):
    """
    >>> create_start_sh('192.168.0.1')
    """
    current_dirname, filename = os.path.split(os.path.abspath(__file__))
    start_sh_name = 'start_vsftpd.sh'
    src_path = f'{current_dirname}/{start_sh_name}'
    dst_path = f'/tmp/{start_sh_name}'
    org_start_sh = misc.open_read(src_path)

    if org_start_sh:
        new_start_sh = org_start_sh.replace('PASV_ADDRESS=127.0.0.1', f'PASV_ADDRESS={pasv_ip}')\
            .replace('FTP_USER=respuser', f'FTP_USER={username}')\
            .replace('FTP_PASS=resppass', f'FTP_PASS={password}')
        misc.open_write(dst_path, new_start_sh)
        return dst_path, start_sh_name
    else:
        print(f'err in create_start_sh: Could not prepare {start_sh_name}')
        exit(1)


def scp_start_sh(pasv_ip, dst_path, password):
    def func(session):
        tmp_start_sh_path, start_sh_name = create_start_sh(pasv_ip)
        ssh.scp(session, tmp_start_sh_path, dst_path, password)

        return start_sh_name
    return func


def scp_local_files(pasv_ip, dst_path, password):
    @session_wrap.bash()
    def func(session):
        scp_docker_image(dst_path, password)(session)
        start_sh_name = scp_start_sh(pasv_ip, dst_path, password)(session)
        return start_sh_name

    return func()


def start(session, pasv_ip, node_dict):
    from recipes import firewalld
    firewalld.configure(ports=['20-21/tcp', '21100-21110/tcp'], add=True)(session)

    username =  node_dict['username']
    password =  node_dict['password']
    access_ip = node_dict['access_ip']
    dst_path = f'{username}@{access_ip}:~'

    vsftpd_start_sh_name = scp_local_files(pasv_ip, dst_path, password)
    [base_shell.run(session, f'docker load -i ~/{image}') for image in [
        'fauria_vsftpd.tar.gz'
    ]]
    base_shell.run(session, 'mkdir -p ~/data/ftpclient')
    base_shell.run(session, 'dd if=/dev/zero of=~/data/ftpclient/one_mega.img bs=1M count=1')
    base_shell.run(session, f'sh ~/{vsftpd_start_sh_name}')
