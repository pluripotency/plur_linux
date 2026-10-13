from plur import base_shell

def set_hostname(hostname):
    return lambda session: base_shell.run(session, f'hostnamectl set-hostname {hostname}')

def disable_ipv6(session):
    base_shell.run(session, 'echo "net.ipv6.conf.all.disable_ipv6 = 1" >> /etc/sysctl.conf')
    base_shell.run(session, 'sysctl -p')

def sudo_apt_update(apt='apt'):
    return f'sudo {apt} update'

def sudo_apt_args_str(args:list[str], nr_auto:bool=False):
    command = 'sudo '
    if nr_auto:
        command = 'sudo NEEDRESTART_MODE=a '
    return command + ' '.join(args) + ' && reset'

def sudo_apt_install_y(pkgs):
    command = sudo_apt_update() + ' && '
    command += sudo_apt_args_str(['DEBIAN_FRONTEND=noninteractive', 'apt', 'install', '-y'] + pkgs)
    return lambda session: base_shell.run(session, command)

def sudo_apt_upgrade(session):
    return base_shell.run(session, sudo_apt_args_str(['apt', 'upgrade', '-y']))

def sudo_apt_get_install_y(pkgs:list[str], nr_auto:bool=False):
    command = sudo_apt_update('apt-get') + ' && '
    command += sudo_apt_args_str(['apt-get', 'install', '-y'] + pkgs, nr_auto=nr_auto)
    return lambda session: base_shell.run(session, command)

def sudo_apt_get_upgrade(session):
    command = sudo_apt_update('apt-get') + ' && '
    command += sudo_apt_args_str(['apt-get', 'upgrade', '-y'])
    return base_shell.run(session, command)

def configure_systemd_timesyncd(session):
    timesyncd_conf = '/etc/systemd/timesyncd.conf'
    add_ntp = 'NTP=ntp.nict.jp'
    base_shell.idempotent_append(session, timesyncd_conf, add_ntp, add_ntp)
    base_shell.run(session, 'timedatectl set-timezone Asia/Tokyo')
    base_shell.run(session, 'systemctl restart systemd-timesyncd')
    base_shell.run(session, 'timedatectl timesync-status')
