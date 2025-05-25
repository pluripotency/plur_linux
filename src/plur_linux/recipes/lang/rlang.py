from plur.base_shell import *
from plur import session_wrap
from recipes import firewalld


# https://docs.rstudio.com/resources/install-r/


def install_dependencies(session):
    # Enable the Extra Packages for Enterprise Linux (EPEL) repository
    action = """
yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
""".split('\n')[1]
    run(session, action)


def symlink(session):
    actions_str = """
ln -s /opt/R/${R_VERSION}/bin/R /usr/local/bin/R
ln -s /opt/R/${R_VERSION}/bin/Rscript /usr/local/bin/Rscript
"""
    actions = actions_str.split('\n')[1:3]
    [run(session, a) for a in actions]


def check_r(session):
    run(session, '')


def install_r(version="3.6.3"):
    actions_str = """
export R_VERSION=%s
curl -O https://cdn.rstudio.com/r/centos-7/pkgs/R-${R_VERSION}-1-1.x86_64.rpm
yum install -y R-${R_VERSION}-1-1.x86_64.rpm
/opt/R/${R_VERSION}/bin/R --version
""" % version
    actions = actions_str.split('\n')[1:4]

    @session_wrap.sudo
    def func(session):
        install_dependencies(session)
        [run(session, a) for a in actions]
        symlink(session)
    return func


@session_wrap.sudo
def install_rstudio_server(session):
    firewalld.configure(ports=['8787'], add=True)(session)
    actions_str = """
curl -O https://download2.rstudio.org/server/centos6/x86_64/rstudio-server-rhel-1.3.1093-x86_64.rpm
yum install -y rstudio-server-rhel-1.3.1093-x86_64.rpm
    """
    actions = actions_str.split('\n')[1:3]
    [run(session, a) for a in actions]

