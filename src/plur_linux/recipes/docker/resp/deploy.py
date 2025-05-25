import os
import re
from plur import session_wrap
from plur import base_shell
from recipes.ops import ssh
from mini import misc


def scp_runner_config(dst_path, password, config_name):
    def func(session):
        src_path = f'/mnt/MC/server_config/mc_conf/resp/{config_name}.toml'
        ssh.scp(session, src_path, f'{dst_path}/config/config.toml', password)
    return func


def scp_docker_image_list(dst_path, password):
    def func(session):
        src_list = [
            'plur3_sniff_runner.tar.gz'
            , 'plur3_sniff_sniffer.tar.gz'
            , 'plur3_sniff_iperf3.tar.gz'
            , 'resp_graph.tar.gz'
            , 'redis.tar.gz'
        ]
        src_path = '/mnt/MC/work_space/archives/docker-images/{' + ','.join(src_list) + '}'
        ssh.scp(session, src_path, dst_path, password)
    return func


def scp_start_sh_list(dst_path, password):
    def func(session):
        current_dirname, filename = os.path.split(os.path.abspath(__file__))
        start_sh_list = [
            'start_redis.sh'
            , 'start_resp_graph.sh'
            , 'arm_cron.sh'
            , 'start_iperf3.sh'
            , 'start_plur3_sniff_runner.sh'
            , 'start_sniffer.sh'
            , 'show_stop_sniffer.sh'
            , 'httping_v0118.sh'
        ]
        src_path = current_dirname + '/{' + ','.join(start_sh_list) + '}'
        ssh.scp(session, src_path, dst_path, password)
        return start_sh_list[:4]
    return func


ex_nginx_dict = {
    'net1': 'v1489',
    'subnet1': '10.5.99.0/24',
    'iface1': 'eth1.1489',
    'ip1': '10.5.99.180',
    'ip1_gw': '10.5.99.254',
    'ip2': '192.168.113.207',
    'nfsen_ip': '10.5.99.217',
}


def extract_nginx_dict(nginx_dict):
    """
    >>> extract_nginx_dict(ex_nginx_dict)
    ['v1489', '10.5.99.0/24', 'eth1.1489', '10.5.99.180', '10.5.99.254', '192.168.113.207', '10.5.99.217']
    """

    net1 = nginx_dict['net1']
    subnet1 = nginx_dict['subnet1']
    iface1 = nginx_dict['iface1']
    ip1 = nginx_dict['ip1']
    ip1_gw = nginx_dict['ip1_gw']
    ip2 = nginx_dict['ip2']
    nfsen_ip = nginx_dict['nfsen_ip']
    return [
        net1,
        subnet1,
        iface1,
        ip1,
        ip1_gw,
        ip2,
        nfsen_ip
    ]


def prepare_nginx_jou_tmp(dst_path, password, nginx_dict):
    [
        net1,
        subnet1,
        iface1,
        ip1,
        ip1_gw,
        ip2,
        nfsen_ip
    ] = extract_nginx_dict(nginx_dict)

    def func(session):
        nginx_jou_dirname = 'nginx_jou'
        tmp_nginx_jou = f'/tmp/{nginx_jou_dirname}'
        current_dirname, filename = os.path.split(os.path.abspath(__file__))
        base_shell.run(session, f'rm -rf {tmp_nginx_jou}')
        base_shell.run(session, f'cp -rf {current_dirname}/{nginx_jou_dirname} {tmp_nginx_jou}')

        ted_conf = misc.open_read(f'{tmp_nginx_jou}/assets/ted.conf')
        misc.open_write(f'{tmp_nginx_jou}/assets/ted.conf', ted_conf.replace('server 172.25.3.217:80;', f'server {nfsen_ip}:80;'))
        start_sh = misc.open_read(f'{tmp_nginx_jou}/start.sh')
        misc.open_write(f'{tmp_nginx_jou}/start.sh', start_sh.replace('NET1=v0002', f'NET1={net1}')
                        .replace('SUBNET1=172.25.0.0/22', f'SUBNET1={subnet1}')
                        .replace('IFACE1=eth1.2', f'IFACE1={iface1}')
                        .replace('IP1=172.25.3.180', f'IP1={ip1}')
                        .replace('IP1_GW=172.25.3.254', f'IP1_GW={ip1_gw}')
                        .replace('IP2=192.168.113.201', f'IP2={ip2}')
                        )

        ssh.scp(session, tmp_nginx_jou, dst_path, password)
        return f'{nginx_jou_dirname}/start.sh'
    return func


def scp_local_files(dst_path, password, config_name, nginx_dict):
    @session_wrap.bash()
    def func(session):
        scp_runner_config(dst_path, password, config_name)(session)
        scp_docker_image_list(dst_path, password)(session)
        start_sh_list = scp_start_sh_list(dst_path, password)(session)
        if nginx_dict:
            nginx_start_sh = prepare_nginx_jou_tmp(dst_path, password, nginx_dict)(session)
            start_sh_list += [nginx_start_sh]
        return start_sh_list
    return func()


def start(session, node_dict, config_name, nginx_dict):
    from recipes import firewalld
    firewalld.configure(ports=['3000/tcp', '5001/udp', '5001/tcp'], add=True)(session)

    work_dir = '~/resp'
    base_shell.run(session, f'mkdir -p {work_dir}/config')
    base_shell.run(session, f'touch {work_dir}/config/config.toml')

    username =  node_dict["username"]
    password =  node_dict["password"]
    access_ip = node_dict["access_ip"]
    dst_path = f'{username}@{access_ip}:{work_dir}'

    start_sh_list = scp_local_files(dst_path, password, config_name, nginx_dict)

    [base_shell.run(session, f'docker load -i {work_dir}/{image}') for image in [
        'redis.tar.gz'
    ]]
    [base_shell.run(session, f'sh {work_dir}/{start_sh}') for start_sh in start_sh_list]





