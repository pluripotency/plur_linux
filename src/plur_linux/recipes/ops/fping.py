import re
import datetime
from plur.base_shell import run, here_doc
from mini import misc


def is_fping_ok(session, hostname_or_ip):
    action = f'fping -r 1 {hostname_or_ip}'
    capture = run(session, action)
    if re.search(f'{hostname_or_ip} is alive', capture):
        return True
    return False


def is_fping_ok_log(log_dir, hostname, access_ip):
    log_path = f'{log_dir}/fping.log'
    now = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')

    def func(session):
        result = False
        if is_fping_ok(session, access_ip):
            line = f'OK\t{hostname}\t{access_ip}\t{now}\n'
            result = True
        else:
            line = f'NG\t{hostname}\t{access_ip}\t{now}\n'
        misc.open_write(log_path, line, 'a')
        return result
    return func


def get_fping_ip_list_result(ip_list, output_path, in_path='/tmp/fping_ip_list.txt'):
    def func(session):
        here_doc(session, in_path, ip_list)
        capt = run(session, f'fping -r 1 < {in_path} |tee {output_path}')
        success_ip_list = []
        for ip in ip_list:
            if re.search(f'{ip} is alive', capt):
                success_ip_list += [ip]
        return success_ip_list
    return func


def get_fping_ip_segment_result(ipv4_with_prefix):
    def func(session):
        capt = run(session, f'fping -r 1 -g {ipv4_with_prefix} 2>&1 | grep -v nreacha ')
        success_ip_list = []
        for line in re.split('\r?\n'):
            if re.search(' is alive', line):
                ip = re.split(' is')[0]
                if misc.is_ipv4(ip):
                    success_ip_list += [ip]
        return success_ip_list
    return func

