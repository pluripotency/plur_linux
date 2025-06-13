from plur.base_shell import *
from plur import session_wrap
from plur_linux.recipes import firewalld

enable_tcp_list = [
    r's/^#\$ModLoad imtcp$/$ModLoad imtcp/'
    , r's/^#\$InputTCPServerRun 514$/$InputTCPServerRun 514/'
]
enable_udp_list = [
    r's/^#\$ModLoad imudp$/$ModLoad imudp/'
    , r's/^#\$UDPServerRun 514$/$UDPServerRun 514/'
]
enable_a8_tcp_list = [
    r's/^#module(load="imtcp") # needs to be done just once$/module(load="imtcp") # needs to be done just once/'
    , r's/^#input(type="imtcp" port="514")$/input(type="imtcp" port="514")/'
]
enable_a8_udp_list = [
    r's/^#module(load="imudp") # needs to be done just once$/module(load="imudp") # needs to be done just once/'
    , r's/^#input(type="imudp" port="514")$/input(type="imudp" port="514")/'
]
ex_rule_list = [
    '$template Test, "/var/log/Test/test.log"'
    , 'if $syslogfacility-text=="local0" and $fromhost-ip=="127.0.0.1" then -?Test'
    , '& ~ # for Test'
]


@session_wrap.sudo
def conf_syslogd_options(session):
    """
    -x: no name resolver, ip only
    -c: console output log level
        5: info
        4: warn
    """
    src_exp = 'SYSLOGD_OPTIONS=""'
    # dst_str = 'SYSLOGD_OPTIONS="-c 5 -x"'
    dst_str = 'SYSLOGD_OPTIONS="-x"'
    target_file_path = '/etc/sysconfig/rsyslog'
    sed_replace_if_exists(session, src_exp, dst_str, target_file_path)


@session_wrap.sudo
def enable_tcp_udp(session):
    file_path = '/etc/rsyslog.conf'
    platform = session.nodes[-1].platform
    if platform in ['almalinux8', 'almalinux9']:
        enable_list = enable_a8_udp_list + enable_a8_tcp_list
    else:
        enable_list = enable_udp_list + enable_tcp_list
    [run(session, f"sed -i '{r}' {file_path}") for r in enable_list]
    firewalld.configure(['syslog'], ports=['514/tcp'], add=True)(session)


@session_wrap.sudo
def enable_udp(session):
    file_path = '/etc/rsyslog.conf'
    platform = session.nodes[-1].platform
    if platform in ['almalinux8', 'almalinux9']:
        enable_list = enable_a8_udp_list
    else:
        enable_list = enable_udp_list
    [run(session, f"sed -i '{r}' {file_path}") for r in enable_list]
    firewalld.configure(['syslog'], add=True)(session)


def replace_rules(rule_list, file_path='/etc/rsyslog.conf'):
    start_exp = '^####PLUR_START'
    end_exp = '^####PLUR_END'

    @session_wrap.sudo
    def func(session):
        delete_between_pattern(file_path, start_exp, end_exp)(session)
        add_lines = [start_exp[1:]]+rule_list+[end_exp[1:]]
        length = len(add_lines)
        while length > 0:
            last_line = add_lines[length-1]
            append_line_after_match(file_path, "#### RULES ####", last_line)(session)
            length -= 1
    return func


def setup(rule_list, enable_tcp=False):
    @session_wrap.sudo
    def func(session):
        if enable_tcp:
            enable_tcp_udp(session)
        else:
            enable_udp(session)
        replace_rules(rule_list)(session)
        service_on(session, 'rsyslog')

    return func
