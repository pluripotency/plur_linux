from plur import base_shell
from plur import session_wrap
from plur_linux.recipes.ops import ops
from plur_linux.recipes import firewalld as conf_firewalld

node_2379 = lambda node_ip: 'http://{0}:2379'.format(node_ip)
node_2380 = lambda node_ip: 'http://{0}:2380'.format(node_ip)


def first_true(iterable, default=False, pred=None):
    """Returns the first true value in the iterable.

    If no true value is found, returns *default*

    If *pred* is not None, returns the first item
    for which pred(item) is true.

    """
    # first_true([a,b,c], x) --> a or b or c or x
    # first_true([a,b], x, f) --> a if f(a) else b if f(b) else x
    return next(filter(pred, iterable), default)


def create_etcd_conf(node_name, node_list, token):
    @session_wrap.sudo
    def func(session):
        etcd_conf = '/etc/etcd/etcd.conf'
        base_shell.create_backup(session, etcd_conf)

        initial_cluster_list = ["{0}={1}".format(n[0], node_2380(n[1])) for n in node_list]
        node_ip = first_true(node_list, pred=lambda n: node_name == n[0])[1]
        lines = [
            'ETCD_NAME=%s' % node_name,
            'ETCD_DATA_DIR="/var/lib/etcd/default.etcd"',
            'ETCD_LISTEN_PEER_URLS="%s"' % node_2380(node_ip),
            'ETCD_LISTEN_CLIENT_URLS="http://0.0.0.0:2379"',
            'ETCD_INITIAL_ADVERTISE_PEER_URLS="%s"' % node_2380(node_ip),
            'ETCD_INITIAL_CLUSTER="%s"' % ','.join(initial_cluster_list),
            'ETCD_INITIAL_CLUSTER_STATE="new"',
            'ETCD_INITIAL_CLUSTER_TOKEN="%s"' % token,
            'ETCD_ADVERTISE_CLIENT_URLS="%s"' % node_2379(node_ip),
        ]
        base_shell.here_doc(session, etcd_conf, lines)
    return func


def start_cluster_by_command(node_name, node_list, token):
    def func(session):
        initial_cluster_list = ["{0}={1}".format(n[0], node_2380(n[1])) for n in node_list]
        node_ip = first_true(node_list, pred=lambda n: node_name == n[0])[1]
        cluster_str = " ".join([
            "sudo etcd",
            "--name %s" % node_name,
            "--initial-advertise-peer-urls %s" % node_2380(node_ip),
            "--listen-peer-urls %s" % node_2380(node_ip),
            "--advertise-client-urls %s" % node_2379(node_ip),
            "--initial-cluster-token %s" % token,
            "--initial-cluster %s" % ",".join(initial_cluster_list),
            "--initial-cluster-state new",
            # "--listen-client-urls %s,http://127.0.0.1:2379" % node_2379(node_ip),
            "&"
        ])
        base_shell.run(session, cluster_str)
        base_shell.here_doc(session, '~/init.sh', [cluster_str])
    return func


def setup(node_name, node_list, token):
    def func(session):
        ops.create_hosts(node_list)(session)
        conf_firewalld.configure(ports=[
            '2379-2380/tcp',    # etcd
        ], add=True)(session)
        base_shell.yum_install(session, {'packages': [
            'etcd'
        ]})

        create_etcd_conf(node_name, node_list, token)(session)
        # base_shell.service_on(session, 'etcd')

    return func


def example_setup_for_etcd1(session):
    token = 'etcd-cluster-1'
    node_list = [
        ['etcd1', '192.168.10.81'],
        ['etcd2', '192.168.10.82'],
        ['etcd3', '192.168.10.83'],
    ]
    setup('etcd1', node_list, token)(session)
