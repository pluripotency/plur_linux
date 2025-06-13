from plur import base_shell
from plur_linux.recipes.ops import user as user_ops, sshd_config


def setup_with_network(session):
    current_node = session.nodes[-1]
    base_shell.ensure_user_sudoer(session)

    session.sudo_i()

    if hasattr(current_node, 'ifaces'):
        from plur_linux.recipes.net import network
        network.configure(current_node)(session)
    if hasattr(current_node, 'ovsinfo'):
        from plur_linux.recipes.centos.open_vswitch import ovs_cmd
        ovs_cmd.configure(session, current_node)
        base_shell.run(session, 'service network restart')
    offline_setup(session, current_node)

    session.su_exit()


def offline_setup(session, node):
    # user must be root
    if node.platform == 'centos6':
        from plur_linux.recipes.centos import ntp
        ntp.configure(session, node)
    elif node.platform in ['centos7']:
        from plur_linux.recipes.centos import chrony
        chrony.configure(session)

    if hasattr(node, 'offline_setups'):
        offline_setups = node.offline_setups
        if 'users' in offline_setups and isinstance(offline_setups['users'], list):
            user_ops.add_users(session, offline_setups['users'])

        if 'sshd_config' in offline_setups:
            sshd_config.apply_and_restart(offline_setups['sshd_config'])(session)
        else:
            sshd_config.apply_and_restart({
                'policy': 'root_without_password',
                'listen': '0.0.0.0'
            })(session)

        if 'iptables' in offline_setups:
            from plur_linux.recipes.centos import iptables
            iptables.setup_iptables(session, offline_setups['iptables'])
        elif 'firewalld' in offline_setups:
            from plur_linux.recipes import firewalld
            firewalld.configure(services=offline_setups['firewalld']['services'], ports=offline_setups['firewalld']['ports'])(session)


def run_setup_list(session, node):
    if hasattr(node, 'setups'):
        setups = node.setups
    else:
        return

    base_shell.ensure_user_sudoer(session)
    if 'run_post' in setups:
        if isinstance(setups['run_post'], list):
            [func(session) for func in setups['run_post']]
        else:
            setups['run_post'](session)
