from plur import base_shell
from plur import session_wrap
from plur_linux.recipes.ops import ops


def install_packages(session):
    base_shell.yum_install(session, [
        'etcd',
        'kubernetes',
        'flannel'
    ])


def conf_etcd(master_ip):
    def f(session):
        filename = '/etc/etcd/etcd.conf'
        base_shell.create_backup(session, filename)
        base_shell.sed_pipe(session, filename + '.org', filename, [
            [
                'ETCD_LISTEN_CLIENT_URLS="http://localhost:2379"',
                'ETCD_LISTEN_CLIENT_URLS="http://%s:2379,http://localhost:2379"' % master_ip
            ]
        ])
        base_shell.run(session, 'systemctl restart etcd')
    return f


def conf_flannel(v_net='172.17.0.0/16'):
    def f(session):
        base_shell.run(session, 'etcdctl mk /atomic.io/network/config \'{"Network":"%s"}\'' % v_net)
        base_shell.run(session, 'systemctl restart flannel')
    return f


@session_wrap.sudo
def setup(session):
    k_master_ip = '10.0.2.30'
    install_packages(session)
    host_list = [
        ['10.0.2.30', 'k-master', 'k-master.r'],
        ['10.0.2.31', 'k-node1', 'k-node1.r'],
    ]
    [f(session) for f in [
        ops.create_hosts(host_list),
        conf_etcd(k_master_ip),
        conf_flannel(),
    ]]
