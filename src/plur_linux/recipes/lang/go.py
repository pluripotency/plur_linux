from plur import session_wrap
from plur import base_shell
go_install_version = 'latest'


def install(version=go_install_version):
    @session_wrap.sudo
    def as_root(session):
        work_dir = '/tmp'
        if version == 'latest':
            base_shell.run(session, 'GOPKG=$(curl https://go.dev/VERSION?m=text | head -n1).linux-amd64.tar.gz')
        else:
            base_shell.run(session, f'GOPKG=go{version}.linux-amd64.tar.gz')
        base_shell.work_on(session, work_dir)
        base_shell.run(session, 'curl -LO https://go.dev/dl/$GOPKG')
        base_shell.run(session, 'rm -rf /usr/local/go && tar -C /usr/local -xzf $GOPKG')

    def func(session):
        as_root(session)
        path_exp = 'export PATH=$PATH:/usr/local/go/bin'
        base_shell.idempotent_append(session, '~/.bashrc', path_exp, path_exp)
        base_shell.run(session, path_exp)
        base_shell.run(session, 'go version')

    return func
