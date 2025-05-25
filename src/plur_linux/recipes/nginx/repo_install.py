import os
from plur import base_shell
from plur import session_wrap
from recipes.ops import ops


def prepare_repo_centos7(session):
    this_dir_path = os.path.dirname(os.path.abspath(__file__))
    base_shell.heredoc_from_local(f'{this_dir_path}/nginx.repos', '/etc/yum.repos.d/nginx.repos')(session)


def preparre_repo_centos6(session):
    base_repo = 'http://nginx.org/packages/'
    repo = base_repo + 'centos/6/noarch/RPMS/nginx-release-centos-6-0.el6.ngx.noarch.rpm'
    base_shell.run(session, 'rpm -ivh ' + repo)


@session_wrap.sudo
def package_install(session):
    if session.platform == 'centos6':
        preparre_repo_centos6(session)
    elif session.platform == 'centos7':
        prepare_repo_centos7(session)
    base_shell.yum_install(session, {'packages': ['nginx']})


def permit_selinux(persist=True):
    @session_wrap.sudo
    def func(session):
        if persist:
            base_shell.run(session, 'setsebool -P httpd_can_network_connect on')
        else:
            base_shell.run(session, 'setsebool httpd_can_network_connect on')
        base_shell.run(session, 'getsebool -a |grep httpd_can_network_connect')
    return func


def install(session):
    package_install(session)
    base_shell.service_on(session, 'nginx')
    ops.disable_selinux(session)
    # permit_selinux()(session)



