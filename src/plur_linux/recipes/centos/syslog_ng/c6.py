from plur import base_shell
from plur import session_wrap


def install_epel(session):
    [base_shell.run(session, action) for action in [
        "wget https://dl.fedoraproject.org/pub/epel/epel-release-latest-6.noarch.rpm",
        "rpm -Uvh epel-release-latest-6.noarch.rpm"
    ]]


def install_syslog_ng(session):
    [base_shell.run(session, action) for action in [
        "cd /etc/yum.repos.d/",
        "wget https://copr.fedorainfracloud.org/coprs/czanik/syslog-ng313epel6/repo/epel-6/czanik-syslog-ng313epel6-epel-6.repo",
        "yum install syslog-ng"
    ]]


@session_wrap.sudo
def setup(session):
    install_epel(session)
    install_syslog_ng(session)
    base_shell.run(session, 'yum erase rsyslog')
