from plur import base_shell

def set_hostname(hostname):
    return lambda session: base_shell.run(session, f'hostnamectl set-hostname {hostname}')

def disable_ipv6(session):
    base_shell.run(session, 'echo "net.ipv6.conf.all.disable_ipv6 = 1" >> /etc/sysctl.conf')
    base_shell.run(session, 'sysctl -p')

def sudo_apt_y_str(args, update=True, apt='apt', nr_auto=False):
    command = ''
    if update:
        command = f'sudo {apt} update && '
    if nr_auto:
        command += f'sudo NEEDRESTART_MODE=a {apt} -y ' + ' '.join(args)
    else:
        command += f'sudo {apt} -y ' + ' '.join(args)
    command += ' && reset'
    return command

def sudo_apt_install_y(pkgs, update=True):
    return lambda session: base_shell.run(session, sudo_apt_y_str(['install'] + pkgs, update))

def sudo_apt_upgrade(session):
    return base_shell.run(session, sudo_apt_y_str(['upgrade']))

def sudo_apt_get_install_y(pkgs, update=True, nr_auto=False):
    return lambda session: base_shell.run(session, sudo_apt_y_str(['install'] + pkgs, update, apt='apt-get', nr_auto=nr_auto))

def sudo_apt_get_upgrade(session):
    return base_shell.run(session, sudo_apt_y_str(['upgrade'], apt='apt-get'))

def configure_systemd_timesyncd(session):
    timesyncd_conf = '/etc/systemd/timesyncd.conf'
    add_ntp = 'NTP=ntp.nict.jp'
    base_shell.idempotent_append(session, timesyncd_conf, add_ntp, add_ntp)
    base_shell.run(session, 'timedatectl set-timezone Asia/Tokyo')
    base_shell.run(session, 'systemctl restart systemd-timesyncd')
    base_shell.run(session, 'timedatectl timesync-status')
