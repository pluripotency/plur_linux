from plur import base_node
from lib import env_ops
from mini import misc
from mini import menu
concat_dict = misc.concat_dict
random_mac = misc.random_mac


def get_waitprompt(overwrite_dict, hostname, login_user):
    if 'platform' in overwrite_dict:
        return base_node.get_linux_waitprompt(overwrite_dict['platform'], hostname, login_user)
    else:
        return base_node.get_linux_waitprompt('centos', hostname, login_user)


def merge_offline_setup(overwrite_dict, user_list):
    if 'offline_setups' in overwrite_dict:
        if 'users' in overwrite_dict['offline_setups']:
            pass
        else:
            overwrite_dict['offline_setups'] = concat_dict([
                overwrite_dict['offline_setups'],
                {
                    'users': user_list,
                }
            ])
    else:
        overwrite_dict['offline_setups'] = {
            'users': user_list,
        }
    return overwrite_dict


def create_node_dict_env_bound(hostname, ifaces, vnets, overwrite_dict={}, login_user='worker', access_ip=None):
    bound_env = env_ops.EnvSegments().bind_env({
        'ifaces': ifaces,
        'vnets': vnets
    })
    user_list = env_ops.get_current_index_user_list()
    login_password = ''
    for user in user_list:
        if user['username'] == login_user:
            login_password = user['password']
    for iface in bound_env['ifaces']:
        if 'access_ip' in iface and iface['access_ip']:
            access_ip = iface['ip'].split('/')[0]
    login_waitprompt = get_waitprompt(overwrite_dict, hostname, login_user)
    overwrite_dict = merge_offline_setup(overwrite_dict, user_list)
    return concat_dict([
        {
            'org_xml': 'rhel7.xml',
            'org_hostname': 'localhost',
            'platform': 'centos7',
            'diskformat': 'qcow2',

            'vcpu': 2,
            'vmem': 2048,

            'access_ip': access_ip,
            'ssh_options': '-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null',
            'ifaces': bound_env['ifaces'],
            'vnets': bound_env['vnets']
        },
        overwrite_dict,
        {

            'hostname': hostname,
            'username': login_user,
            'password': login_password,
            'waitprompt': login_waitprompt,
        }
    ])


def create_single_iface_node_dict(hostname, ip_seed=None, option={}, login_user='worker'):
    if ip_seed is None:
        ip_seed = menu.get_input(r'(dhcp|\d+)', 'IP seed(Default: dhcp): ', 'invalid format', 'dhcp')
    vnets = [{
        'ifname': 'eth0',
        'mac': random_mac()
    }]
    if 'ifaces' in option:
        ifaces = option['ifaces']
        overwrite_dict = {k: v for k, v in option.items() if k not in ['ifaces']}
    else:
        ifaces = [{
            'access_ip': True,
            'con_name': 'eth0',
            'autoconnect': True,
            'ip_seed': ip_seed
        }]
        overwrite_dict = option

    return create_node_dict_env_bound(hostname, ifaces, vnets, overwrite_dict, login_user)


def destroy_node_dict(hostname, overwrite_dict={}):
    sp = hostname.split('.')
    if len(sp) > 1:
        hostname = sp[0]
    return concat_dict([
        {
            'hostname': hostname,
        },
        overwrite_dict
    ])


def destroy_node(hostname, overwrite_dict={}):
    return base_node.Node(destroy_node_dict(hostname, overwrite_dict))


def create_kvm_dict(hostname, access_ip, overwrite_dict={}, username='root', platform='centos7'):
    user_list = env_ops.get_current_index_user_list()
    login_password = ''
    for user in user_list:
        if user['username'] == username:
            login_password = user['password']
    login_waitprompt = base_node.get_linux_waitprompt(platform, hostname, username)
    return misc.concat_dict([
        {
            'ssh_options': '-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null',
            'access_ip': access_ip,
            'offline_setups': {
                'users': user_list
            }
        },
        overwrite_dict,
        {
            'platform': platform,
            'hostname': hostname,
            'username': username,
            'password': login_password,
            'waitprompt': login_waitprompt
        }
    ])
